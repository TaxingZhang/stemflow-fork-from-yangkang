"""This file is to store static functions for multi-processing

"""
import copy

#
import warnings
from typing import Tuple, Union
from warnings import simplefilter

import numpy as np
import pandas as pd
from numpy import ndarray

# validation check
from pandas.core.frame import DataFrame
from sklearn.base import BaseEstimator
from sklearn.utils import class_weight

from ..utils.jitterrotation.jitterrotator import JitterRotator
from .dummy_model import dummy_model1

# warnings.filterwarnings("ignore")


def train_one_stixel(
    stixel_training_size_threshold: int,
    x_names: Union[list, np.ndarray],
    task: str,
    base_model: BaseEstimator,
    sample_weights_for_classifier: bool,
    subset_x_names: bool,
    stixel_X_train: pd.core.frame.DataFrame,
) -> Tuple[Union[None, BaseEstimator], list]:
    """Train one stixel

    Args:
        stixel_training_size_threshold (int): Only stixels with data points above this threshold are trained.
        x_names (Union[list, np.ndarray]): Total x_names. Predictor variable.s
        task (str): One of 'regression', 'classification' and 'hurdle'
        base_model (BaseEstimator): Base model estimator.
        sample_weights_for_classifier (bool): Whether to balance the sample weights in classifier for imbalanced samples.
        subset_x_names (bool): Whether to only store variables with std > 0 for each stixel.
        sub_X_train (pd.core.frame.DataFrame): Input training dataframe for THE stixel.

    Returns:
        tuple[Union[None, BaseEstimator], list]: trained_model, stixel_specific_x_names
    """

    if len(stixel_X_train) < stixel_training_size_threshold:  # threshold
        return (None, [], "Not_Enough_Data")

    sub_y_train = stixel_X_train["true_y"]
    sub_X_train = stixel_X_train[x_names]
    unique_sub_y_train_binary = np.unique(np.where(sub_y_train > 0, 1, 0))

    # nan check
    nan_count = np.sum(np.isnan(np.array(sub_X_train))) + np.sum(np.isnan(sub_y_train))
    if nan_count > 0:
        return (None, [], "Contain_Nan")

    # fit
    if (not task == "regression") and (len(unique_sub_y_train_binary) == 1):
        trained_model = dummy_model1(float(unique_sub_y_train_binary[0]))
        return (trained_model, [], "Success")
    else:
        # Remove the variables that have no variation
        stixel_specific_x_names = x_names.copy()

        if subset_x_names:
            stixel_specific_x_names = [
                i for i in stixel_specific_x_names if i not in list(sub_X_train.columns[sub_X_train.std(axis=0) == 0])
            ]

        # continue, if no variable left
        if len(stixel_specific_x_names) == 0:
            return (None, [], "x_names_length_zero")

        # now we are sure to fit a model
        trained_model = copy.deepcopy(base_model)

        if (not task == "regression") and sample_weights_for_classifier:
            sample_weights = class_weight.compute_sample_weight(
                class_weight="balanced", y=np.where(sub_y_train > 0, 1, 0)
            )

            try:
                trained_model.fit(sub_X_train[stixel_specific_x_names], sub_y_train, sample_weight=sample_weights)

            except Exception as e:
                print(e)
                # raise
                return (None, [], "Base_model_fitting_error(non-regression, balanced weight)")
        else:
            try:
                trained_model.fit(sub_X_train[stixel_specific_x_names], sub_y_train)

            except Exception as e:
                print(e)
                # raise
                return (None, [], "Base_model_fitting_error(regression)")

    return (trained_model, stixel_specific_x_names, "Success")


def assign_points_to_one_ensemble(
    ensemble_df: pd.core.frame.DataFrame,
    ensemble: str,
    Sample_ST_df: pd.core.frame.DataFrame,
    Temporal1: str,
    Spatio1: str,
    Spatio2: str,
    feature_importances_: pd.core.frame.DataFrame,
) -> pd.core.frame.DataFrame:
    """assign points to one ensemble

    Args:
        ensemble_df (pd.core.frame.DataFrame): ensemble_df
        ensemble (str): name of the ensemble
        Sample_ST_df (pd.core.frame.DataFrame): input sample spatio-temporal points of interest
        Temporal1 (str): Temporal variable name 1
        Spatio1 (str): Spatio variable name 1
        Spatio2 (str): Spatio variable name 2
        feature_importances_ (pd.core.frame.DataFrame): feature_importances_ dataframe

    Returns:
        A DataFrame containing the aggregated feature importance
    """
    this_ensemble = ensemble_df[ensemble_df.ensemble_index == ensemble]
    this_ensemble.loc[:, "stixel_calibration_point_transformed_left_bound"] = [
        i[0] for i in this_ensemble["stixel_calibration_point(transformed)"]
    ]

    this_ensemble.loc[:, "stixel_calibration_point_transformed_lower_bound"] = [
        i[1] for i in this_ensemble["stixel_calibration_point(transformed)"]
    ]

    this_ensemble.loc[:, "stixel_calibration_point_transformed_right_bound"] = (
        this_ensemble["stixel_calibration_point_transformed_left_bound"] + this_ensemble["stixel_width"]
    )

    this_ensemble.loc[:, "stixel_calibration_point_transformed_upper_bound"] = (
        this_ensemble["stixel_calibration_point_transformed_lower_bound"] + this_ensemble["stixel_height"]
    )

    Sample_ST_df_ = transform_pred_set_to_STEM_quad(
        Spatio1, Spatio2, Sample_ST_df.reset_index(drop=True), this_ensemble
    )

    # pred each stixel
    res_list = []
    for index, line in this_ensemble.iterrows():
        stixel_index = line["unique_stixel_id"]
        sub_Sample_ST_df = Sample_ST_df_[
            (Sample_ST_df_[Temporal1] >= line[f"{Temporal1}_start"])
            & (Sample_ST_df_[Temporal1] < line[f"{Temporal1}_end"])
            & (Sample_ST_df_[f"{Spatio1}_new"] >= line["stixel_calibration_point_transformed_left_bound"])
            & (Sample_ST_df_[f"{Spatio1}_new"] <= line["stixel_calibration_point_transformed_right_bound"])
            & (Sample_ST_df_[f"{Spatio2}_new"] >= line["stixel_calibration_point_transformed_lower_bound"])
            & (Sample_ST_df_[f"{Spatio2}_new"] <= line["stixel_calibration_point_transformed_upper_bound"])
        ]

        if len(sub_Sample_ST_df) == 0:
            continue

        # load feature_importances
        try:
            this_feature_importance = feature_importances_[feature_importances_["stixel_index"] == stixel_index]
            if len(this_feature_importance) == 0:
                continue
            this_feature_importance = dict(this_feature_importance.iloc[0, :])
            res_list.append(
                {
                    "sample_index": list(sub_Sample_ST_df.index),
                    **{
                        a: [b] * len(sub_Sample_ST_df)
                        for a, b in zip(this_feature_importance.keys(), this_feature_importance.values())
                    },
                }
            )

        except Exception as e:
            print(e)
            continue

    res_list = pd.concat([pd.DataFrame(i) for i in res_list], axis=0).drop("stixel_index", axis=1)
    res_list = res_list.groupby("sample_index").mean().reset_index(drop=False)
    return res_list


def transform_pred_set_to_STEM_quad(
    Spatio1: str, Spatio2: str, X_train: pd.core.frame.DataFrame, ensemble_info: pd.core.frame.DataFrame
) -> pd.core.frame.DataFrame:
    """Project the input data points to the space of quadtree stixels.

    Args:
        Spatio1 (str):
            Name of the spatio column 1
        Spatio2 (str):
            Name of the spatio column 2
        X_train (pd.core.frame.DataFrame):
            Training/Testing variables
        ensemble_info (pd.core.frame.DataFrame):
            the DataFrame with information of the stixel.

    Returns:
        Projected X_train

    """

    angle = float(ensemble_info["rotation"].iloc[0])
    calibration_point_x_jitter = float(ensemble_info["space_jitter(first rotate by zero then add this)"].iloc[0][0])
    calibration_point_y_jitter = float(ensemble_info["space_jitter(first rotate by zero then add this)"].iloc[0][1])

    X_train_ = X_train.copy()
    a, b = JitterRotator.rotate_jitter(
        X_train[Spatio1], X_train[Spatio2], angle, calibration_point_x_jitter, calibration_point_y_jitter
    )
    X_train_[f"{Spatio1}_new"] = a
    X_train_[f"{Spatio2}_new"] = b

    return X_train_


def get_model_by_name(model_dict: dict, ensemble: str, grid_index: str) -> Union[None, BaseEstimator]:
    """get_model_by_name

    Args:
        model_dict (dict): self.model_dict. Dictionary of trained models.
        ensemble (str): ensemble name.
        grid_index (str): grid index

    Returns:
        The trained model.
    """
    try:
        model = model_dict[f"{ensemble}_{grid_index}_model"]
        return model
    except Exception as e:
        warnings.warn(f"Cannot find model: {e}")
        return None


def get_stixel_specific_name_by_model(
    model: Union[None, BaseEstimator], stixel_specific_x_names_dict: dict, x_names: list, ensemble: str, grid_index: str
) -> Union[None, list]:
    """get_stixel_specific_name_by_model

    Args:
        model (Union[None, BaseEstimator]): model of this stixel
        stixel_specific_x_names_dict (dict): the stixel_specific_x_names dictionary. Generated after training.
        x_names (list): total x_names. All variables.
        ensemble (str): ensemble name.
        grid_index (str): grid index.

    Returns:
        stixel specific x_names.
    """
    if model is None:
        return None

    if isinstance(model, dummy_model1):
        stixel_specific_x_names = x_names
    else:
        stixel_specific_x_names = stixel_specific_x_names_dict[f"{ensemble}_{grid_index}"]

    return stixel_specific_x_names


def get_model_and_stixel_specific_x_names(
    model_dict: dict, ensemble: str, grid_index: str, stixel_specific_x_names_dict: dict, x_names: list
) -> Tuple[Union[None, BaseEstimator], list]:
    """get_model_and_stixel_specific_x_names

    Args:
        model_dict (dict): self.model_dict. Dictionary of trained models.
        ensemble (str): ensemble name.
        grid_index (str): grid index.
        stixel_specific_x_names_dict (dict): the stixel_specific_x_names dictionary. Generated after training.
        x_names (list): Total x_names. All variables.

    Returns:
       A tuple of (model, stixel_specific_x_names) for this stixel
    """
    model = get_model_by_name(model_dict, ensemble, grid_index)
    stixel_specific_x_names = get_stixel_specific_name_by_model(
        model, stixel_specific_x_names_dict, x_names, ensemble, grid_index
    )
    return model, stixel_specific_x_names


def predict_one_stixel(
    X_test_stixel: pd.core.frame.DataFrame,
    task: str,
    model_x_names_tuple: Tuple[Union[None, BaseEstimator], list],
) -> pd.core.frame.DataFrame:
    """predict_one_stixel

    Args:
        X_test_copy (pd.core.frame.DataFrame): Input testing variables
        task (str): One of 'regression', 'classification' and 'hurdle'
        model_x_names_tuple (tuple[Union[None, BaseEstimator], list]): A tuple of (model, stixel_specific_x_names)

    Returns:
        A Dataframe of predicted results. With 'index' the same as the input indexes.
    """
    if model_x_names_tuple[0] is None:
        return None

    if len(X_test_stixel) == 0:
        return None

    # get test data
    if task == "regression":
        pred = model_x_names_tuple[0].predict(np.array(X_test_stixel[model_x_names_tuple[1]]))
    else:
        pred = model_x_names_tuple[0].predict_proba(np.array(X_test_stixel[model_x_names_tuple[1]]))[:, 1]

    res = pd.DataFrame({"index": list(X_test_stixel.index), "pred": np.array(pred).flatten()}).set_index("index")

    return res
