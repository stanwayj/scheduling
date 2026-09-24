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

def get_block_signature(block):
    """
    Extracts a unique, hashable tuple signature for an ObservingBlock.
    Survives multiprocessing serialization / pickling.
    """
    if hasattr(block, "target") and block.target is not None:
        target_id = block.target.name
    else:
        target_id = str(block)
        
    duration_val = block.duration.value if hasattr(block.duration, "value") else str(block.duration)
    priority_val = getattr(block, "priority", None)
    
    return (target_id, duration_val, priority_val)


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

def merge_schedules(schedules, start_time=None, end_time=None, allow_overlaps=True):
    """
    Merges multiple Schedule objects into a master schedule by constructing clean Slot
    instances and assigning master_schedule.slots directly.
    """
    if not schedules:
        raise ValueError("At least one Schedule must be provided to merge.")

    if start_time is None:
        start_time = min(s.start_time for s in schedules)
    if end_time is None:
        end_time = max(s.end_time for s in schedules)

    master_schedule = Schedule(start_time, end_time)

    # Collect occupied slots
    all_slots = []
    for sched in schedules:
        for slot in sched.slots:
            if slot.block is not None:
                all_slots.append(slot)

    # Sort chronologically
    all_slots.sort(key=lambda s: s.start)

    merged_slots = []
    last_end_time = None

    for slot in all_slots:
        if last_end_time is not None and slot.start < last_end_time:
            sig = get_block_signature(slot.block)
            msg = f"Overlap detected for '{sig[0]}' starting at {slot.start.iso}"
            if not allow_overlaps:
                raise ValueError(msg)
            else:
                continue  # Skip conflicting overlapping slot

        # Construct new Slot instance and preserve block assignment
        new_slot = Slot(slot.start, slot.end)
        new_slot.block = slot.block
        merged_slots.append(new_slot)
        
        last_end_time = slot.end

    master_schedule.slots = merged_slots
    return master_schedule

def extract_unscheduled_blocks(original_blocks, master_schedule):
    """
    Extracts unscheduled blocks by matching explicit integer block IDs.
    """
    # Collect IDs of all blocks currently in the schedule
    scheduled_ids = set()
    for slot in master_schedule.slots:
        if slot.block is not None and hasattr(slot.block, "block_id"):
            scheduled_ids.add(slot.block.block_id)

    # Return original blocks whose IDs are missing from scheduled_ids
    unscheduled = [
        block for block in original_blocks 
        if getattr(block, "block_id", None) not in scheduled_ids
    ]
    
    return unscheduled

def fill_remaining_slots(master_schedule, unscheduled_blocks, observer, transitioner, time_resolution, constraints=None):
    """Fills open slots in master_schedule with remaining blocks using a single core."""
    if not unscheduled_blocks:
        return master_schedule
        
    secondary_scheduler = PriorityScheduler(
        constraints=constraints,
        observer=observer,
        transitioner=transitioner,
        time_resolution=time_resolution
    )

    return secondary_scheduler(unscheduled_blocks, master_schedule)


def construct_schedule(config, constraints, transitioner, blocks):

    observer = Observer.at_site(config['telescope']['observatory'])

    start_time = Time(config['observations']['start_date'] + " " + config['observations']['start_time'], format='iso')
    end_time = Time(config['observations']['end_date'] + " " + config['observations']['end_time'], format='iso')

    time_resolution = config['misc']['time_resolution'] * u.second

    for idx, block in enumerate(blocks):
        block.block_id = idx

    schedules = parallel_priority_schedule(blocks, observer, start_time, end_time, transitioner, time_resolution, constraints, 4)
    master_schedule = merge_schedules(schedules, allow_overlaps=True)

    unscheduled_blocks = extract_unscheduled_blocks(blocks, master_schedule)
    print(f"Blocks scheduled in parallel: {len(blocks) - len(unscheduled_blocks)} / {len(blocks)}")
    print(f"Unscheduled blocks remaining : {len(unscheduled_blocks)}")

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
