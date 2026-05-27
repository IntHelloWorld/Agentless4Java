import json
import os
import pickle

res_file = "/home/qyh/projects/Agentless4Java/results/defects4j/file_level/loc_outputs.jsonl"
dataset_dir = "/home/qyh/projects/Agentless4Java/data/defects4j"

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
        dic = structure['structure']
        keys = file_name.split("/")
        for key in keys:
            if key in dic:
                dic = dic[key]
            else:
                break
        if 'classes' not in dic:
            continue
        
        for method in methods:
            class_name = method.split(".")[0]
            method_name = method.split(".")[1]
            for clazz in dic['classes']:
                if clazz['name'] == class_name:
                    for method in clazz['methods']:
                        if method['name'] == method_name:
                            output.append({
                                'file_name': file_name,
                                'class_name': class_name,
                                'method_name': method_name,
                                'start_line': method['start_line'],
                                'end_line': method['end_line']
                            })
    return output

with open(res_file, "r") as f:
    
    all_res = {}
    top_1_bugs = []
    top_5_bugs = []
    
    for line in f:
        line = line.strip()
        if line == "":
            continue
        
        res = json.loads(line)
        instance_id = res['instance_id']
        
        # get buggy methods
        dataset_file = os.path.join(dataset_dir, instance_id.replace("@", "_"), 'snippet.json')
        buggy_methods = []
        with open(dataset_file, "r") as f:
            snippets = json.load(f)
            for snippet in snippets:
                if snippet['is_bug']:
                    buggy_methods.append(snippet)
        
        # get rank
        find_class = False
        found_files = res['found_files'][:1]
        for method in buggy_methods:
            if method['class_name'].replace(".", "/") + '.java' in found_files:
                find_class = True
                break
        
        proj, bug_id = instance_id.split("@")
        if proj not in all_res:
            all_res[proj] = {"class_level": 0}
        
        if find_class:
            all_res[proj]["class_level"] += 1

    print(json.dumps(all_res, indent=4))