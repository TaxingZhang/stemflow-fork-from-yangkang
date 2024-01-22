
from sklearn.base import BaseEstimator
from typing import Union
import numpy as np
import pandas as pd
import warnings

def _monkey_patched_predict_proba(
    model: BaseEstimator, X_train: Union[pd.core.frame.DataFrame, np.ndarray]
) -> np.ndarray:
    """the monkey patching predict_proba method

    Args:
        model: the input model
        X_train: input training data

    Returns:
        predicted proba
    """
    pred = model.predict(X_train)
    pred = np.array(pred).reshape(-1, 1)
    return np.concatenate([np.zeros(shape=pred.shape), pred], axis=1)


def model_wrapper(model: BaseEstimator) -> BaseEstimator:
    """wrap a predict_proba function for those models who don't have

    Args:
        model:
            Input model

    Returns:
        Wrapped model that has a `predict_proba` method

    """
    if "predict_proba" in dir(model):
        return model
    else:
        warnings.warn("predict_proba function not in base_model. Monkey patching one.")

        model.predict_proba = _monkey_patched_predict_proba
        return model
    