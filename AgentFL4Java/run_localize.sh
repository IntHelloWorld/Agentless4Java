export PYTHONPATH=$PYTHONPATH:$(pwd)

# python agentless/fl/localize.py --file_level \
#                                 --output_folder results/defects4j/file_level \
#                                 --num_threads 8 \
#                                 --skip_existing

# python agentless/fl/localize.py --file_level \
#                                 --irrelevant \
#                                 --output_folder results/defects4j/file_level_irrelevant \
#                                 --num_threads 12 \
#                                 --skip_existing

# python agentless/fl/retrieve.py --index_type simple \
#                                 --filter_type given_files \
#                                 --filter_file results/defects4j/file_level_irrelevant/loc_outputs.jsonl \
#                                 --output_folder results/defects4j/retrievel_embedding \
#                                 --persist_dir embedding/defects4j \
#                                 --num_threads 1

python agentless/fl/combine.py  --retrieval_loc_file results/defects4j/retrievel_embedding/retrieve_locs.jsonl \
                                --model_loc_file results/defects4j/file_level/loc_outputs.jsonl \
                                --top_n 3 \
                                --output_folder results/defects4j/file_level_combined

python agentless/fl/localize.py --related_level \
                                --output_folder results/defects4j/related_elements \
                                --top_n 5 \
                                --compress_assign \
                                --compress \
                                --start_file results/defects4j/file_level_combined/combined_locs.jsonl \
                                --num_threads 10 \
                                --skip_existing

# python agentless/fl/localize.py --related_level \
#                                 --output_folder results/defects4j/related_elements_no_rag \
#                                 --top_n 5 \
#                                 --compress_assign \
#                                 --compress \
#                                 --start_file results/defects4j/file_level/loc_outputs.jsonl \
#                                 --num_threads 10 \
#                                 --skip_existing