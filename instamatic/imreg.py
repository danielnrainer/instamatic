from numpy.fft import fft2, ifft2, fftshift

def translation(im0, im1, return_fft=False):
    """Return translation vector to register images.

    TODO: doc
    """
    shape = im0.shape
    f0 = fft2(im0)
    f1 = fft2(im1)
    ir = abs(ifft2((f0 * f1.conjugate()) / (abs(f0) * abs(f1))))
    t0, t1 = np.unravel_index(np.argmax(ir), shape)
    if t0 > shape[0] // 2:
        t0 -= shape[0]
    if t1 > shape[1] // 2:
        t1 -= shape[1]
    
    if return_fft:
        return [t0, t1], ir
    else:
        return [t0, t1]
