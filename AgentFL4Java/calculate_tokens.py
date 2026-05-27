import re
from pathlib import Path

import tiktoken
from tqdm import tqdm

result_dir = Path("/home/qyh/projects/Agentless4Java/results/defects4j")


def count_tokens_openai(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def get_tokens(log_file):
    in_text = []
    out_text = ""
    with log_file.open("r") as f:
        for line in f:
            if "prompting with message:" in line:
                line = f.readline()
                while "- INFO -" not in line:
                    line = f.readline()
                    in_text.append(line)

            if "API response ChatCompletion" in line:
                out_text = re.search(r"content=(.*?), ", line, re.DOTALL)
                if out_text:
                    out_text = out_text.group(1)

    in_tokens = count_tokens_openai("".join(in_text))
    out_tokens = count_tokens_openai(out_text)
    return in_tokens, out_tokens


file_level_logs_dir = result_dir / "file_level" / "localization_logs"
file_level_irrelevant_logs_dir = (
    result_dir / "file_level_irrelevant" / "localization_logs"
)
related_elements_logs_dir = (
    result_dir / "related_elements" / "localization_logs"
)
dirs = [
    file_level_logs_dir,
    file_level_irrelevant_logs_dir,
    related_elements_logs_dir,
]

tokens = {}
for log_dir in dirs:
    for log_file in tqdm(
        log_dir.glob("*.log"), desc=f"Processing logs in {log_dir.name}"
    ):
        bug_name = log_file.stem
        in_tokens, out_tokens = get_tokens(log_file)
        if bug_name not in tokens:
            tokens[bug_name] = {"in_tokens": 0, "out_tokens": 0}
        tokens[bug_name]["in_tokens"] += in_tokens
        tokens[bug_name]["out_tokens"] += out_tokens

# Calculate the mean and standard deviation of in and out tokens respectively
mean_in_tokens = sum(token["in_tokens"] for token in tokens.values()) / len(
    tokens
)
mean_out_tokens = sum(token["out_tokens"] for token in tokens.values()) / len(
    tokens
)

std_in_tokens = (
    sum(
        (token["in_tokens"] - mean_in_tokens) ** 2 for token in tokens.values()
    )
    / len(tokens)
) ** 0.5
std_out_tokens = (
    sum(
        (token["out_tokens"] - mean_out_tokens) ** 2
        for token in tokens.values()
    )
    / len(tokens)
) ** 0.5

print(f"Mean in tokens: {mean_in_tokens}, Std in tokens: {std_in_tokens}")
print(f"Mean out tokens: {mean_out_tokens}, Std out tokens: {std_out_tokens}")
