import argparse
import concurrent.futures
import json
import os
from threading import Lock

from datasets import load_dataset
from tqdm import tqdm

from AgentFL4Java.dataset import ALL_BUGS
from agentless.fl.Index import EmbeddingIndex
from agentless.util.preprocess_data import (
    filter_none_java,
    filter_none_python,
    filter_out_test_files,
    get_repo_structure,
)
from agentless.util.utils import load_json, load_jsonl, setup_logger


def retrieve_locs(
    bug, args, swe_bench_data, found_files, prev_o, write_lock=None
):

    found = False
    for o in prev_o:
        if o["instance_id"] == bug["instance_id"]:
            found = True
            break

    if found:
        logger.info(
            f"skipping {bug['instance_id']} since patch already generated"
        )
        return None

    instance_id = bug["instance_id"]

    if args.target_id is not None:
        if args.target_id != instance_id:
            return None

    log_file = os.path.join(
        args.output_folder, "retrieval_logs", f"{instance_id}.log"
    )
    logger = setup_logger(log_file)
    logger.info(f"Processing bug {instance_id}")

    # bench_data = [x for x in swe_bench_data if x["instance_id"] == instance_id][0]
    # problem_statement = bench_data["problem_statement"]
    problem_statement = None
    structure = get_repo_structure(
        instance_id,
        bug["repo"],
        bug["base_commit"],
        bug["subproj"],
        "playground",
    )

    # filter_none_python(structure)
    filter_none_java(structure)
    # filter_out_test_files(structure)

    if args.filter_file:
        kwargs = {  # build retrieval kwargs
            "given_files": [
                x for x in found_files if x["instance_id"] == instance_id
            ][0]["found_files"],
            "filter_top_n": args.filter_top_n,
        }
    else:
        kwargs = {}

    # main retrieval
    retriever = EmbeddingIndex(
        instance_id,
        structure,
        problem_statement,
        persist_dir=args.persist_dir,
        filter_type=args.filter_type,
        index_type=args.index_type,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        logger=logger,
        **kwargs,
    )

    file_names, meta_infos, traj = retriever.retrieve(mock=args.mock)

    # if write_lock is not None:
    #     write_lock.acquire()
    tmp_output_folder = os.path.join(args.output_folder, "tmp")
    os.makedirs(tmp_output_folder, exist_ok=True)
    tmp_output_file = os.path.join(tmp_output_folder, f"{instance_id}.json")
    with open(tmp_output_file, "w") as f:
        f.write(
            json.dumps(
                {
                    "instance_id": instance_id,
                    "found_files": file_names,
                    "node_info": meta_infos,
                    "traj": traj,
                }
            )
        )
    # if write_lock is not None:
    #     write_lock.release()


def retrieve(args):
    if args.filter_file:
        found_files = load_jsonl(args.filter_file)
    else:
        found_files = []

    # swe_bench_data = load_dataset(args.dataset, split="test")
    swe_bench_data = None
    prev_o = (
        load_jsonl(args.output_file)
        if os.path.exists(args.output_file)
        else []
    )

    bugs = []
    for version in ALL_BUGS:
        for proj in ALL_BUGS[version]:
            subproj = (
                ALL_BUGS[version][proj][2]
                if version == "GrowingBugs"
                else None
            )
            for bug_id in ALL_BUGS[version][proj][0]:
                if bug_id in ALL_BUGS[version][proj][1]:
                    continue
                instance_id = f"{proj}@{bug_id}"
                bug = {
                    "instance_id": instance_id,
                    "repo": proj,
                    "base_commit": None,
                    "subproj": subproj,
                }
                tmp_res_file = os.path.join(
                    args.output_folder, "tmp", f"{bug['instance_id']}.json"
                )
                if os.path.exists(tmp_res_file):
                    print(f"skipping {bug['instance_id']}")
                else:
                    bugs.append(bug)

    if args.num_threads == 1:
        for bug in tqdm(bugs, colour="MAGENTA"):
            retrieve_locs(
                bug, args, swe_bench_data, found_files, prev_o, write_lock=None
            )
    else:
        write_lock = Lock()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.num_threads
        ) as executor:
            # futures = [
            #     executor.submit(
            #         retrieve_locs,
            #         bug,
            #         args,
            #         swe_bench_data,
            #         found_files,
            #         prev_o,
            #         write_lock,
            #     )
            #     for bug in bugs
            # ]
            futures = []
            for bug in bugs:
                tmp_res_file = os.path.join(
                    args.output_folder, "tmp", f"{bug['instance_id']}.json"
                )
                if os.path.exists(tmp_res_file):
                    print(f"skipping {bug['instance_id']}")
                else:
                    futures.append(
                        executor.submit(
                            retrieve_locs,
                            bug,
                            args,
                            swe_bench_data,
                            found_files,
                            prev_o,
                            write_lock,
                        )
                    )
            for _ in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(bugs),
                colour="MAGENTA",
            ):
                pass

    print(os.getcwd())
    tmp_output_folder = os.path.join(args.output_folder, "tmp")
    with open(args.output_file, "w") as f:
        for file in os.listdir(tmp_output_folder):
            with open(os.path.join(tmp_output_folder, file), "r") as f_tmp:
                f.write(f_tmp.read() + "\n")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output_folder",
        type=str,
        default="results/defects4j/retrievel_embedding",
    )
    parser.add_argument(
        "--output_file", type=str, default="retrieve_locs.jsonl"
    )
    parser.add_argument(
        "--index_type",
        type=str,
        default="simple",
        choices=["simple", "complex"],
    )
    parser.add_argument(
        "--filter_type",
        type=str,
        default="given_files",
        choices=["none", "given_files"],
    )
    parser.add_argument("--filter_top_n", type=int, default=100)
    parser.add_argument(
        "--filter_file",
        type=str,
        default="results/defects4j/file_level_irrelevant/loc_outputs.jsonl",
    )
    parser.add_argument("--chunk_size", type=int, default=512)
    parser.add_argument("--chunk_overlap", type=int, default=0)
    parser.add_argument(
        "--persist_dir", type=str, default="embedding/defects4j"
    )
    parser.add_argument("--target_id", type=str)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument(
        "--num_threads",
        type=int,
        default=1,
        help="Number of threads to use for creating API requests (WARNING, embedding token counts are only accurate when thread=1)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="princeton-nlp/SWE-bench_Lite",
        choices=[
            "princeton-nlp/SWE-bench_Lite",
            "princeton-nlp/SWE-bench_Verified",
        ],
    )

    args = parser.parse_args()

    args.output_file = os.path.join(args.output_folder, args.output_file)
    assert (
        not args.filter_type == "given_files" or args.filter_file != ""
    ), "Need to provide a filtering file"

    os.makedirs(args.output_folder, exist_ok=True)
    os.makedirs(
        os.path.join(args.output_folder, "retrieval_logs"), exist_ok=True
    )

    # dump argument
    with open(os.path.join(args.output_folder, "args.json"), "w") as f:
        json.dump(vars(args), f, indent=4)

    retrieve(args)


if __name__ == "__main__":
    main()
