from __future__ import annotations

import numpy as np
from pycsou.core import LinearOperator
from pycsou.func import SquaredL2Loss, L1Norm
from pycsou.linop import DenseLinearOperator
from pycsou.opt import APGD, PrimalDualSplitting

from src.solver import Solver, MyOperator


class LassoSolver(Solver):

    def __init__(self, y: np.ndarray, operator: np.ndarray, lambda_: float,
                 penalty_operator: None | np.ndarray | LinearOperator = None) -> None:
        super().__init__(y, operator)
        self.lambda_ = lambda_
        self.penalty_operator = penalty_operator

    def solve(self) -> (np.ndarray, np.ndarray):
        H = MyOperator(self.operator)
        H.compute_lipschitz_cst()

        l22_loss = (1 / 2) * SquaredL2Loss(H.shape[0], self.y)
        F = l22_loss * H

        G = self.lambda_ * L1Norm(H.shape[1])

        if self.penalty_operator is None:
            apgd = APGD(self.operator.shape[1], F=F, G=G, verbose=None)
            estimate, converged, diagnostics = apgd.iterate()
            x = estimate['iterand']
        else:
            if isinstance(self.penalty_operator, LinearOperator):
                D = self.penalty_operator
            else:
                D = DenseLinearOperator(self.penalty_operator)
                D.compute_lipschitz_cst()
            pds = PrimalDualSplitting(self.operator.shape[1], F=F, H=G, K=D, verbose=None)
            estimate, converged, diagnostics = pds.iterate()
            x = estimate['primal_variable']

        return x, x
