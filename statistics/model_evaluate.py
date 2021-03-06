import os
import re
import sys
import numpy as np
import pathlib

sys.path.append(os.path.abspath("../"))
import config
from util import data_loader
from util import data_visualization as dv
from util import keras_util
from util import path

y_val = {}
for i in range(1, 6):
    val1_train_files, val1_val_files = data_loader.get_k_fold_files("1.txt", i, [config.DATA_TYPE_SEGMENTED],
                                                                    shuffle=False)
    y_val[i] = np.array(data_loader.get_labels(val1_val_files), np.bool)


def check_invalid_model(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if "model" in file and "val" in file and ".py" in file and "pyc" not in file:
                record_dir = os.path.join(os.path.join(root, "record"), file.split("_")[0])
                record_dir = os.path.join(record_dir, file.split("_")[1].split(".")[0])

                weight_path = os.path.join(record_dir,
                             "%sweights.%03d.hdf5" % (str([str(j) for j in range(13)]), 3))

                unique_path = re.match(r".*competition[\\/]*(.*)", weight_path).group(1)
                real_weight_file = os.path.join("E:\\backup\\jdfc", pathlib.Path(unique_path))
                if not os.path.exists(real_weight_file):
                    if "val3" in real_weight_file:
                        print("%s" % os.path.join(root, file))

def predict_tta_all(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if "model" in file and "val" in file and ".py" in file and "pyc" not in file:
                print("start predict tta %s" % os.path.join(root, file))
                model_name = file.split(".")[0]
                attr_get_model, attr_model_config = keras_util.dynamic_model_import(
                    model_path_in=os.path.join(root, model_name))
                model = attr_get_model(output_dim=len(attr_model_config.label_position), weights=None)
                attr_model_config.predict_tta_all(model)


def predict_models(path, val_index=1):
    for root, dirs, files in os.walk(path):
        if ("val%d" % val_index) in os.path.split(root)[-1]:
            weights_files = []
            predict_files = []
            evaluate_files = []
            for file in files:
                if file.split(".")[-1] == "hdf5":
                    weights_files.append(os.path.join(root, file))
                elif "predict" in file:
                    predict_files.append(os.path.join(root, file))
                elif "evaluate" in file:
                    evaluate_files.append(os.path.join(root, file))

            if len(weights_files) == 0 and len(predict_files) == 0:
                continue

            # 因为考虑到磁盘空间问题，可能会将Model Weight放到另外的目录
            if len(weights_files) <= len(predict_files) and len(evaluate_files) != 0:
                print("skip %s" % root)
                continue

            for i in evaluate_files:
                os.remove(i)

            weights_file_sorted = {}
            for weights_file in weights_files:
                index = re.match(r".*weights\.0*(.*)\.hdf5", weights_file).group(1)
                weights_file_sorted[int(index) - 1] = weights_file
            weights_file_sorted = [weights_file_sorted[k] for k in sorted(weights_file_sorted.keys())]

            # for weights_file in weights_file_sorted:
            #     attr_get_model, attr_model_config = keras_util.dynamic_model_import(weights_file)
            #     attr_model_config.current_epoch = int(re.match(r".*weights\.0*(.*)\.hdf5", weights_file).group(1))
            #
            #     print("evaluate :%s" % weights_file)
            #     if keras_util.get_prediction_path(weights_file) not in predict_files:
            #         model = attr_get_model(output_dim=len(attr_model_config.label_position), weights=None)
            #         model.load_weights(weights_file)
            #         y_pred = keras_util.predict_tta(model, attr_model_config, verbose=1)
            #         keras_util.save_prediction_file(y_pred, weights_file)

            predict_files = [os.path.join(root_dir, predict_f) for root_dir, _, predict_fs in os.walk(root) for
                             predict_f in predict_fs if "predict" in predict_f]

            predict_file_sorted = {}
            for predict_file in predict_files:
                index = re.match(r".*weights\.0*(.*)\.hdf5", predict_file).group(1)
                predict_file_sorted[int(index) - 1] = predict_file
            predict_file_sorted = [predict_file_sorted[k] for k in sorted(predict_file_sorted.keys())]

            for predict_file in predict_file_sorted:
                model_file = "_".join(re.match(r".*record\\(.*)\\\[", predict_file).group(1).split("\\"))
                model_dir = re.match(r"(.*)\\record", predict_file).group(1)
                model_path = os.path.join(model_dir, model_file)
                root_dir, type_dir, name = re.match(r".*competition\\(.*)", model_path).group(1).split("\\")
                package = __import__(".".join([root_dir, type_dir, name]))
                attr_model_config = getattr(getattr(getattr(package, type_dir), name), "model_config")
                attr_model_config.current_epoch = int(re.match(r".*weights\.0*(.*)\.hdf5", predict_file).group(1))
                # dv.show_label_calss_bar_per_epoch(attr_model_config.train_files, attr_model_config.record_dir)
                y_pred = np.load(predict_file)

                print(f"predict {predict_file}")
                keras_util.evaluate(y_val[val_index], y_pred, keras_util.get_weight_path(predict_file),
                                    attr_model_config)




predict_models(os.path.join(path.MODEL_PATH), 1)
predict_models(os.path.join(path.MODEL_PATH), 2)
predict_models(os.path.join(path.MODEL_PATH), 3)
predict_models(os.path.join(path.MODEL_PATH), 4)
predict_models(os.path.join(path.MODEL_PATH), 5)

# if __name__ == '__main__':
#     predict_tta_all(path.MODEL_PATH)
    # check_invalid_model(path.MODEL_PATH)