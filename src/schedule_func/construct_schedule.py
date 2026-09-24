import concurrent.futures
import multiprocessing
import numpy as np

import astroplan
from astroplan import Observer, ObservingBlock, TransitionBlock

from astroplan.scheduling import PriorityScheduler, Schedule, Slot

from astropy.time import Time, TimeDelta
import astropy.units as u
import time

"""
def construct_schedule(config, constraints, transitioner, blocks):

    ## Observatory ##
    observer = Observer.at_site(config['telescope']['observatory'])

    ## Start and End dates ##
    start_time = Time(config['observations']['start_date'] + " " + config['observations']['start_time'], format='iso')
    end_time = Time(config['observations']['end_date'] + " " + config['observations']['end_time'], format='iso')

    ## Time resolution of schedule ##
    time_resolution = config['misc']['time_resolution'] * u.second

    ## Initialise schedule with constraints and transition ##
    prior_scheduler = PriorityScheduler(constraints = constraints,
                                        observer = observer,
                                        transitioner = transitioner,
                                        time_resolution = time_resolution)

    ## Schedule the observing blocks ##
    priority_schedule = Schedule(start_time, end_time)
    prior_scheduler(blocks, priority_schedule) # This is the step that takes a long time

    ## Convert schedule to Dataframe and return to central script ##
    df = priority_schedule.to_table().to_pandas()
    return df
"""


def chunk_blocks(blocks, num_chunks):
    """Splits a list of observing blocks into n roughly equal chunks."""
    k, m = divmod(len(blocks), num_chunks)
    return [
        blocks[i * k + min(i, m):(i + 1) * k + min(i + 1, m)]
        for i in range(num_chunks)
    ]


def run_scheduler_worker(args):
    """Worker function executed on individual CPU cores."""
    blocks_chunk, observer, time_range, constraints, transitioner, time_resolution = args
    
    # Initialize process-local scheduler
    scheduler = PriorityScheduler(
        constraints=constraints,
        observer=observer,
        transitioner=transitioner,
        time_resolution=time_resolution
    )
    
    schedule = Schedule(time_range[0], time_range[1])
    scheduled_result = scheduler(blocks_chunk, schedule)
    return scheduled_result


def parallel_priority_schedule(blocks, observer, start_time, end_time, transitioner, time_resolution, constraints=None, num_cores=None):
    
    if num_cores is None:
        num_cores = multiprocessing.cpu_count()

    block_chunks = chunk_blocks(blocks, num_cores)

    window_duration = TimeDelta(14 * u.day)
    step_offset = TimeDelta(1 * u.day)

    # Construct unique, non-overlapping or offset time ranges for each core
    task_args = []
    for i, chunk in enumerate(block_chunks):
        if len(chunk) == 0:
            continue
            
        # Calculate distinct start and end times for subgroup i
        chunk_start = start_time + (i * window_duration) + step_offset
        chunk_end = chunk_start + window_duration
        time_range = (chunk_start, chunk_end)
        
        task_args.append((chunk, observer, time_range, constraints, transitioner, time_resolution))

    schedules = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
        for sched in executor.map(run_scheduler_worker, task_args):
            if sched is not None:
                schedules.append(sched)

    return schedules

def merge_schedules(schedules, start_time=None, end_time=None, allow_overlaps=False):
    """
    Merges multiple astroplan.scheduling.Schedule objects into a single master schedule
    by directly populating the master_schedule.slots list attribute.
    """
    if not schedules:
        raise ValueError("At least one Schedule must be provided to merge.")

    if start_time is None:
        start_time = min(s.start_time for s in schedules)
    if end_time is None:
        end_time = max(s.end_time for s in schedules)

    # 1. Instantiate master schedule with boundaries
    master_schedule = Schedule(start_time, end_time)

    # 2. Extract all non-empty occupied slots
    all_slots = []
    for sched in schedules:
        for slot in sched.slots:
            if slot.block is not None:
                all_slots.append(slot)

    # 3. Sort chronologically by start time
    all_slots.sort(key=lambda s: s.start)

    # 4. Check overlaps and construct fresh Slot instances
    merged_slots = []
    last_end_time = None

    for slot in all_slots:
        if last_end_time is not None and slot.start < last_end_time:
            block_identifier = (
                slot.block.target.name 
                if hasattr(slot.block, "target") 
                else str(slot.block)
            )
            msg = f"Overlap detected for '{block_identifier}' starting at {slot.start.iso}"
            if not allow_overlaps:
                raise ValueError(msg)
            else:
                print(f"[Warning] {msg}")
                continue

        # Create clean Slot and attach block
        new_slot = Slot(slot.start, slot.end)
        new_slot.block = slot.block
        merged_slots.append(new_slot)
        
        last_end_time = slot.end

    # 5. Overwrite internal slot list directly
    master_schedule.slots = merged_slots
    return master_schedule

def extract_unscheduled_blocks(original_blocks, schedule):
    """
    Identifies unscheduled ObservingBlocks by matching unique attributes
    (target name, priority, and duration) instead of Python object memory IDs.
    """
    # Build a set of unique signatures for blocks present in the schedule
    scheduled_signatures = set()
    
    for slot in schedule.slots:
        if slot.block is not None:
            block = slot.block
            # Use target name + duration + priority as a unique identifier
            if hasattr(block, "target") and block.target is not None:
                sig = (block.target.name, block.duration, getattr(block, "priority", None))
            else:
                sig = (str(block), block.duration, getattr(block, "priority", None))
            scheduled_signatures.add(sig)

    # Filter out blocks from original_blocks that match scheduled signatures
    unscheduled_blocks = []
    for block in original_blocks:
        if hasattr(block, "target") and block.target is not None:
            sig = (block.target.name, block.duration, getattr(block, "priority", None))
        else:
            sig = (str(block), block.duration, getattr(block, "priority", None))
            
        if sig not in scheduled_signatures:
            unscheduled_blocks.append(block)

    return unscheduled_blocks


def fill_remaining_slots(master_schedule, unscheduled_blocks, observer, transitioner, time_resolution, constraints=None):
    """
    Runs a single-core PriorityScheduler pass to insert unscheduled blocks 
    into remaining open slots of an existing master schedule.
    """
    # Initialize scheduler with constraints and observer
    secondary_scheduler = PriorityScheduler(
        constraints=constraints,
        observer=observer,
        transitioner=transitioner,
        time_resolution = time_resolution
    )
    
    # Run the scheduler using the existing master_schedule as target
    filled_schedule = secondary_scheduler(unscheduled_blocks, master_schedule)
    return filled_schedule


def construct_schedule(config, constraints, transitioner, blocks):

    observer = Observer.at_site(config['telescope']['observatory'])

    start_time = Time(config['observations']['start_date'] + " " + config['observations']['start_time'], format='iso')
    end_time = Time(config['observations']['end_date'] + " " + config['observations']['end_time'], format='iso')

    time_resolution = config['misc']['time_resolution'] * u.second

    schedules = parallel_priority_schedule(blocks, observer, start_time, end_time, transitioner, time_resolution, constraints, 4)
    master_schedule = merge_schedules(schedules, allow_overlaps=True)
    print(master_schedule)
    unscheduled_blocks = extract_unscheduled_blocks(blocks, master_schedule)
    print(f"Unscheduled blocks remaining: {len(unscheduled_blocks)}")

    # 4. Fill remaining open gaps using a single-core pass
    final_schedule = fill_remaining_slots(
        master_schedule, 
        unscheduled_blocks, 
        observer, 
        transitioner,
        time_resolution,
        constraints)

    ## Schedule the observing blocks ##
    #priority_schedule = Schedule(start_time, end_time)
    #start_time = time.time()
    #prior_scheduler(blocks, priority_schedule) # This is the step that takes a long time
    #print("Time taken - ", time.time() - start_time)
    #prior_scheduler(blocks[84:160], priority_schedule)

    ## Convert schedule to Dataframe and return to central script ##
    df = final_schedule.to_table().to_pandas()
    return df
