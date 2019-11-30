import encode
import decode
import numpy as np
import utility
from PIL import Image
if __name__ == '__main__':
    image = 'sailboat.bmp'
    image_input = Image.open(image).convert('L')
    matrix_input = np.asarray(image_input)
    matrix_input = matrix_input.astype(int)
    message = [i % 2 for i in range(0, 37026)]
    matrix_output = encode.encode(matrix_input, message)
    matrix_output_t = matrix_output.copy()
    image_output = Image.fromarray(matrix_output).convert('L')
    image_output.save('output_' + image)
    matrix_output = decode.decode(matrix_output)
    matrix_input = np.asarray(image_input)
    err = np.sum(np.square(matrix_input - matrix_output))
    print('error: {}'.format(err))
    height, width = matrix_input.shape
    for i in range(height):
        for j in range(width):
            if matrix_input[i][j] != matrix_output[i][j]:
                print('({},{})'.format(i, j))
    print('psnr: {}'.format(utility.psnr(matrix_input, matrix_output_t)))

