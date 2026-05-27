import json
import os
import pickle

from tqdm import tqdm

res_file = "/home/qyh/projects/Agentless4Java/results/defects4j/related_elements/loc_outputs.jsonl"
dataset_dir = "/home/qyh/projects/Agentless4Java/data/defects4j"
structure_dir = "/home/qyh/projects/Agentless4Java/results/defects4j/structure"

res_dict = {}


def parse_agentless_res(raw_output):
    output = {}
    for line in raw_output.split("\n"):
        if line == "":
            continue
        elif line.startswith("method:"):
            buggy_method = line.split(":")[1].strip()
            class_name = buggy_method.split(".")[0]
            for file_name in output:
                if f"{class_name}.java" in file_name:
                    output[file_name].append(buggy_method)
        elif line.endswith(".java"):
            file_name = line.strip()
            if file_name not in output:
                output[file_name] = []
    return output


def add_loc_info(agentless_res, structure):
    output = []
    for file_name, methods in agentless_res.items():
        dic = structure["structure"]
        keys = file_name.split("/")
        for key in keys:
            if key in dic:
                dic = dic[key]
            else:
                break
        if "classes" not in dic:
            continue

        for method in methods:
            try:
                class_name = method.split(".")[0]
                method_name = method.split(".")[1]
                for clazz in dic["classes"]:
                    if clazz["name"] == class_name:
                        for method in clazz["methods"]:
                            if method["name"] == method_name:
                                output.append(
                                    {
                                        "file_name": file_name,
                                        "class_name": class_name,
                                        "method_name": method_name,
                                        "start_line": method["start_line"],
                                        "end_line": method["end_line"],
                                    }
                                )
            except:
                continue
    return output


def calculate_average_precision(buggy_methods, agentless_res):
    """Calculate Average Precision for a single bug instance"""
    if not buggy_methods or not agentless_res:
        return 0.0

    relevant_count = 0
    precision_sum = 0.0

    for rank, loc in enumerate(agentless_res, 1):
        is_relevant = False
        for method in buggy_methods:
            if (
                loc["file_name"] in method["src_path"]
                and loc["start_line"] == method["begin_line"]
            ):
                is_relevant = True
                break

        if is_relevant:
            relevant_count += 1
            precision_at_k = relevant_count / rank
            precision_sum += precision_at_k

    return (
        precision_sum / len(buggy_methods) if len(buggy_methods) > 0 else 0.0
    )


def calculate_reciprocal_rank(buggy_methods, agentless_res):
    """Calculate Reciprocal Rank for a single bug instance"""
    if not buggy_methods or not agentless_res:
        return 0.0

    for rank, loc in enumerate(agentless_res, 1):
        for method in buggy_methods:
            if (
                loc["file_name"] in method["src_path"]
                and loc["start_line"] == method["begin_line"]
            ):
                return 1.0 / rank

    return 0.0


with open(res_file, "r") as f:

    all_res = {}
    overall_ap_scores = []
    overall_rr_scores = []
    top_1_bugs = []
    top_5_bugs = []
    mfr_all = []
    mar_all = []

    for line in tqdm(f):
        line = line.strip()
        if line == "":
            continue

        res = json.loads(line)
        instance_id = res["instance_id"]
        structure_file = os.path.join(structure_dir, f"{instance_id}.pkl")
        agentless_res = parse_agentless_res(
            res["additional_artifact_loc_related"][0]["raw_output_loc"]
        )
        structure = pickle.load(open(structure_file, "rb"))
        agentless_res = add_loc_info(agentless_res, structure)

        # get buggy methods
        dataset_file = os.path.join(
            dataset_dir, instance_id.replace("@", "_"), "snippet.json"
        )
        buggy_methods = []
        with open(dataset_file, "r") as f:
            snippets = json.load(f)
            for snippet in snippets:
                if snippet["is_bug"]:
                    buggy_methods.append(snippet)

        # Calculate AP and RR for this instance
        ap_score = calculate_average_precision(buggy_methods, agentless_res)
        rr_score = calculate_reciprocal_rank(buggy_methods, agentless_res)
        overall_ap_scores.append(ap_score)
        overall_rr_scores.append(rr_score)

        # get rank (modified to handle multiple buggy methods)
        top_rank = float("inf")
        find_class = False
        found_methods = set()

        matched_indexes = []
        for rank, loc in enumerate(agentless_res, 1):
            for method in buggy_methods:
                if loc["file_name"] in method["src_path"]:
                    find_class = True
                if (
                    loc["file_name"] in method["src_path"]
                    and loc["start_line"] == method["begin_line"]
                ):
                    method_key = f"{method['src_path']}:{method['begin_line']}"
                    if method_key not in found_methods:
                        matched_indexes.append(rank)
                        top_rank = min(top_rank, rank)
                        found_methods.add(method_key)

        if matched_indexes == []:
            matched_indexes = [51]

        if top_rank == float("inf"):
            top_rank = 51

        proj, bug_id = instance_id.split("@")
        if proj not in all_res:
            all_res[proj] = {
                "total": 0,
                "top1": 0,
                "top3": 0,
                "top5": 0,
                "top10": 0,
                "class_level": 0,
                "ap_scores": [],
                "rr_scores": [],
                "map": 0.0,
                "mrr": 0.0,
                "mfr": [],
                "mar": [],
            }

        all_res[proj]["total"] += 1
        all_res[proj]["ap_scores"].append(ap_score)
        all_res[proj]["rr_scores"].append(rr_score)

        if top_rank == 1:
            all_res[proj]["top1"] += 1
            top_1_bugs.append(f"{proj}-{bug_id}")
        if 0 < top_rank <= 3:
            all_res[proj]["top3"] += 1
        if 0 < top_rank <= 5:
            all_res[proj]["top5"] += 1
            top_5_bugs.append(f"{proj}-{bug_id}")
        if 0 < top_rank <= 10:
            all_res[proj]["top10"] += 1

        all_res[proj]["mfr"].append(top_rank)
        all_res[proj]["mar"].append(
            sum(matched_indexes) / len(matched_indexes)
        )

        if find_class:
            all_res[proj]["class_level"] += 1

    for proj in all_res:
        if all_res[proj]["mfr"]:
            mfr_all.extend(all_res[proj]["mfr"])
            all_res[proj]["mfr"] = sum(all_res[proj]["mfr"]) / len(
                all_res[proj]["mfr"]
            )
        else:
            all_res[proj]["mfr"] = None

        if all_res[proj]["mar"]:
            mar_all.extend(all_res[proj]["mar"])
            all_res[proj]["mar"] = sum(all_res[proj]["mar"]) / len(
                all_res[proj]["mar"]
            )
        else:
            all_res[proj]["mar"] = None

    # Calculate MAP and MRR for each project
    for proj in all_res:
        if all_res[proj]["ap_scores"]:
            all_res[proj]["map"] = sum(all_res[proj]["ap_scores"]) / len(
                all_res[proj]["ap_scores"]
            )
        if all_res[proj]["rr_scores"]:
            all_res[proj]["mrr"] = sum(all_res[proj]["rr_scores"]) / len(
                all_res[proj]["rr_scores"]
            )
        # Remove raw scores from output for cleaner results
        del all_res[proj]["ap_scores"]
        del all_res[proj]["rr_scores"]

    # Calculate overall metrics
    overall_metrics = {
        "total_bugs": len(overall_ap_scores),
        "overall_map": (
            sum(overall_ap_scores) / len(overall_ap_scores)
            if overall_ap_scores
            else 0.0
        ),
        "overall_mrr": (
            sum(overall_rr_scores) / len(overall_rr_scores)
            if overall_rr_scores
            else 0.0
        ),
        "projects": all_res,
    }

    with open("evaluate_result.json", "w") as f:
        json.dump(overall_metrics, f, indent=4)
    print(json.dumps(overall_metrics, indent=4))
    print(f"Total MFR: {sum(mfr_all) / len(mfr_all)}")
    print(f"Total MAR: {sum(mar_all) / len(mar_all)}")

    with open("Agentless_top1.txt", "w") as f:
        f.write("\n".join(top_1_bugs))
    with open("Agentless_top5.txt", "w") as f:
        f.write("\n".join(top_5_bugs))
