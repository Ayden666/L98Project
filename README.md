# L98Project

## Task 1

For task 1, the files in `/DeepBank1.1` have been modified and the associated FrameNet information has been added to the DeepBank EDS node.

For example, in `/DeepBank1.1/20001001`, the node e3 becomes

e3:_join_v_1**-fn.Cause_to_amalgamate**<34:38>{e SF prop, TENSE fut, MOOD indicative, PROG -, PERF -}[ARG1**-fn.Agent** x6, ARG2**-fn.Part_1** x23]

The FrameNet frame Cause_to_amalgamate was added to the predicate and the FrameNet roles Agent and Part_1 were added to its arguments.

The predicates that were properly labeled were extracted and saved in `train.csv`, this becomes the training data in task 2. The predicates that were labeled as IN/NF were also extracted and saved in `predict.csv`, this is the data to be predicted in tsak 2.

## Task 2

For task 2, a Convolutional Neural Network was trained on the data in `train.csv`, and the model is then used to predict the FrameNet frames for the nodes in `predict.csv`. The outcome of the prediction is saved in `pred_output.csv`.
