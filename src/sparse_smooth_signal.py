from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy import sparse
import matplotlib.pyplot as plt
from pycsou.linop.sampling import MappedDistanceMatrix


class SparseSmoothSignal:
    """
    Base class for the sparse and smooth signal.

    The signal is composed of 2 signals, one sparse and one smooth, x = x_sparse + x_smooth
    yo is the prefect signal obtained through a linear measurement operator H of the signal such that y0 = H @ x
    y is the signal yo with some error represented by a gaussian white noise

    Attributes
    ----------

    dim : Tuple[int ,int]
        shape of the signal x
    sparse : np.ndarray
        matrix representing the sparse part of the signal
    smooth : np.ndarray
        matrix representing the smooth part of the signal
    x : np.ndarray
        signal x sum of sparse and smooth
    measurement_operator : np.ndarray 
        matrix representing the linear sensing measurement operator used
    H : np.ndarray 
        alias for measurement_operator
    psnr : np.float64
         peak signal-to-noise ratio of the gaussian white noise added
    noise :
        gaussian white noise added
    yo : np.ndarray
        prefect output signal
    y : np.ndarray
        output signal

    Methods
    -------
    random_sparse() -> None
        Creates a new random sparse component
    random_smooth() -> None
        Creates a new random smooth component
    random_measurement_operator(size: int) -> None
        Creates a new random measurement operator with size random lines of the DFT matrix
    gaussian_noise(psnr: np.float64 = None) -> None:
        Creates a new gaussian white noise
    plot() -> None
        Plot all signals in 2d
    show() -> None
        Show the plotted signals, it is used after plot()
        needed if we want to plot multiple SparseSmoothSignal
    """

    # cache measurements operators
    __operators = {}

    def __init__(self, dim: Tuple[int, int], sparse: None | np.ndarray = None, smooth: None | np.ndarray = None,
                 measurement_operator: None | np.ndarray = None, psnr: np.float64 = 50):
        """
        Parameters
        ----------
        dim : Tuple[int ,int]
            shape of the signal x
        sparse : None | np.ndarray
            matrix representing the sparse part of the signal
        smooth : None | np.ndarray
            matrix representing the smooth part of the signal
        measurement_operator : None | np.ndarray 
            matrix representing the linear sensing measurement operator used
        psnr : np.float64
            peak signal-to-noise ratio of the gaussian white noise added

        For any optionnal argumant if not specified the corresponding value will be random 
        except variance which is 1 by default
        """
        assert dim[0] >= 0 and dim[1] >= 0, "Negative dimension is not valid"

        self.__dim = dim
        # length of the signal x
        self.__size = dim[0] * dim[1]
        # length of the output signal y
        self.__y_size = self.__size

        self.__psnr = psnr

        # cache
        self.__x = None
        self.__y0 = None
        self.__y = None
        self.__noise = None

        if sparse is not None:
            assert sparse.shape == dim, "Sparse is not the same shape as dim"
            self.__sparse = sparse
        else:
            self.random_sparse()

        if smooth is not None:
            assert smooth.shape == dim, "Smooth is not the same size as dim"
            self.__smooth = smooth
        else:
            self.random_smooth()

        if measurement_operator is not None:
            assert measurement_operator.shape[1] == self.__size, "Measurement operator shape does not match dim"
            self.__measurement_operator = measurement_operator
        else:
            self.random_measurement_operator()

    @property
    def dim(self) -> Tuple[int, int]:
        return self.__dim

    @property
    def sparse(self) -> np.ndarray:
        return self.__sparse.toarray()

    @sparse.setter
    def sparse(self, value: np.ndarray) -> None:
        self.__sparse = value
        # delete deprecated cached values
        self.__x = None
        self.__y0 = None
        self.__y = None

    @property
    def smooth(self) -> np.ndarray:
        return self.__smooth

    @smooth.setter
    def smooth(self, value: np.ndarray) -> None:
        self.__smooth = value
        # delete deprecated cached values
        self.__x = None
        self.__y0 = None
        self.__y = None

    @property
    def measurement_operator(self) -> np.ndarray:
        return self.__measurement_operator

    @measurement_operator.setter
    def measurement_operator(self, value: np.ndarray) -> None:
        self.__measurement_operator = value
        # delete deprecated cached values
        self.__y0 = None
        self.__y = None
        self.gaussian_noise()

    @property
    def H(self) -> np.ndarray:
        return self.measurement_operator

    @H.setter
    def H(self, value: np.ndarray) -> None:
        self.measurement_operator = value

    @property
    def x(self) -> np.ndarray:
        if self.__x is None:
            self.__x = self.__sparse.toarray() + self.__smooth
        return self.__x

    @property
    def y0(self) -> np.ndarray:
        if self.__y0 is None:
            self.__y0 = self.H @ self.x.ravel()
        return self.__y0

    @property
    def y(self) -> np.ndarray:
        if self.__y is None:
            self.__y = self.y0 + self.__noise
        return self.__y

    @property
    def noise(self) -> np.ndarray:
        return self.__noise

    @noise.setter
    def noise(self, value: np.ndarray) -> None:
        self.__noise = value
        # delete deprecated cached values
        self.__y0 = None

    def random_sparse(self) -> None:
        """
        Creates a new random sparse component
        """
        rand_matrix = 4 * sparse.rand(self.__dim[0], self.__dim[1], density=0.005)
        rand_matrix.data += 2
        self.sparse = rand_matrix

    def random_smooth(self) -> None:
        """
        Creates a new random smooth component
        """
        # number of gaussian we create
        nb = int(0.005 * self.__size)

        # grid
        x = np.linspace(-1, 1, self.__dim[0])
        y = np.linspace(-1, 1, self.__dim[1])
        x, y = np.meshgrid(x, y)
        samples1 = np.stack((x.flatten(), y.flatten()), axis=-1)
        # random gaussian's centers
        rng = np.random.default_rng()
        samples2 = np.stack((2 * rng.random(size=nb) - 1, 2 * rng.random(size=nb) - 1), axis=-1)

        sigma = 1/5
        # used to reduce computation time
        max_distance = 3 * sigma
        # gaussian
        func = lambda x: np.exp(-x ** 2 / (2 * sigma ** 2))
        MDMOp = MappedDistanceMatrix(samples1=samples1, samples2=samples2, function=func, max_distance=max_distance,
                                     operator_type='dask')
        alpha = np.ones(samples2.shape[0])
        m = MDMOp * alpha
        self.smooth = (m / np.max(m)).reshape(self.__dim[0], self.__dim[1])

    def random_measurement_operator(self, size: int = None) -> None:
        """
        Creates a new random measurement operator with size random lines of the DFT matrix

        Parameters
        ----------
        size :
            Numbers of lines of the DFT matrix we want to pick, witch is also the new dimension of y
        """
        if size is None:
            size = self.__y_size
        else:
            assert self.__size >= size >= 0
            self.__y_size = size
        rand = np.random.choice(self.__size, size, replace=False)
        # check if the operators is cached
        if self.__dim in self.__operators.keys():
            op = self.__operators[self.__dim]
        else:
            op = self.create_measurement_operator(self.__dim)
            # cache the new operators and remove one if cache full
            if len(self.__operators) > 10:
                self.__operators.popitem()
            else:
                self.__operators[self.__dim] = op
        self.measurement_operator = op[rand]

    def gaussian_noise(self, psnr: np.float64 = None) -> None:
        """
        Creates a new gaussian white noise

        Parameters
        ----------
        psnr :
            peak signal-to-noise ratio of the gaussian white noise
            if None then we choose the last input
            if the psnr was never changed we take 10
        """
        if psnr is None:
            psnr = self.__psnr
        else:
            self.__psnr = psnr
        y0_max = np.max(np.abs(self.y0))
        # mean squared error in decibel
        mse_db = 20 * np.log10(y0_max) - psnr
        # convert mean squared error from db to watts
        mse = 10 ** (mse_db / 10)

        # mse is the variance of the noise and since it is a complex gaussian the variance is halved
        self.noise = np.random.normal(0, np.sqrt(mse / 2), (self.__y_size, 2)).view(np.complex128)

    def plot(self) -> None:
        """
        Plot all signals in 2d
        """
        fig, ax = plt.subplots()
        fig.canvas.set_window_title('Spare + Smooth Signal')
        fig.suptitle("X")
        im = ax.imshow(self.x)
        fig.colorbar(im, ax=ax)
        ax.axis('off')

        fig, ax = plt.subplots()
        fig.canvas.set_window_title('Spare + Smooth Signal')
        fig.suptitle("Smooth")
        im = ax.imshow(self.smooth)
        fig.colorbar(im, ax=ax)
        ax.axis('off')

        fig, ax = plt.subplots()
        fig.canvas.set_window_title('Spare + Smooth Signal')
        fig.suptitle("Spare")
        im = ax.imshow(self.sparse)
        fig.colorbar(im, ax=ax)
        ax.axis('off')


    @classmethod
    def show(cls) -> None:
        """
        Show the plotted signals, it is used after plot()
        needed if we want to plot multiple SparseSmoothSignal
        """
        plt.show()

    @staticmethod
    def create_measurement_operator(dim: Tuple[int, int]) -> np.ndarray:
        # we create 100 images of dimension dim
        base = np.zeros((dim[0] * dim[1], dim[0], dim[1]))
        # we create the indexing array to put ones at the right place to create the bases
        index_img = np.arange(0, dim[0] * dim[1])
        index_x = np.kron(np.arange(0, dim[0]), np.ones(dim[0], dtype=int))
        index_y = np.kron(np.ones(dim[1], dtype=int), np.arange(0, dim[1]))
        base[index_img, index_x, index_y] = 1
        # compute fft2 over the two last dimension
        dtf_2d = np.fft.fft2(base)
        # flatten the two last dimensions
        operator = dtf_2d.reshape(dim[0] * dim[1], dim[0] * dim[1])
        return operator