# Reconstruction of composite sparse-plus-smooth images using mixed penalties
This is the repository of my bachelor's project. The project goal is to write a python framework that solves discrete linear inverse problems on 2D composite sparse-plus-smooth signals. These signals are the sum of two components, a sparse one and the other one smooth. The goal is to reconstruct these type of signals given a number of linear measurements made by some linear operator. More specificly, in my project I have apply this to radio astronomy where we need to reconstruct images from radio measurements. Here the sparse-plus-smooth signal is an image that representes the light intensity from space that we want to recover, the measurements are made by a subsampling of the 2D DFT. My goal is to reconstruct the original image from these few measurements and anaylse how this sparse-plus-smooth assumption on the original signal inpactes the reconstructed signal.
