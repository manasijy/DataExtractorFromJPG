# python extract_and_scale.py --img aa2219Data.jpg --num 25 --out extracted_points.csv
import matplotlib.pyplot as plt
import csv
import argparse

def get_scaling_parameters(img_path):
    """
    Interactively get scaling parameters for x and y axes.
    User clicks two reference points for each axis and enters their actual values.
    Returns: (x_ref_pixels, x_ref_values, y_ref_pixels, y_ref_values)
    """
    img = plt.imread(img_path)
    plt.imshow(img)
    plt.title('Click two reference points on the X axis, then two on the Y axis.\nClose the window after selecting.')
    ref_points = plt.ginput(4, timeout=0)
    plt.close()
    print("Reference points (pixels):", ref_points)

    print("Enter actual values for the two X axis reference points:")
    x_val1 = float(input("Actual value for first X point: "))
    x_val2 = float(input("Actual value for second X point: "))
    print("Enter actual values for the two Y axis reference points:")
    y_val1 = float(input("Actual value for first Y point: "))
    y_val2 = float(input("Actual value for second Y point: "))

    x_ref_pixels = [ref_points[0][0], ref_points[1][0]]
    x_ref_values = [x_val1, x_val2]
    y_ref_pixels = [ref_points[2][1], ref_points[3][1]]
    y_ref_values = [y_val1, y_val2]

    print("Scaling parameters set.")
    return x_ref_pixels, x_ref_values, y_ref_pixels, y_ref_values

def pixel_to_data(x_pixel, y_pixel, x_ref_pixels, x_ref_values, y_ref_pixels, y_ref_values):
    x_scale = (x_ref_values[1] - x_ref_values[0]) / (x_ref_pixels[1] - x_ref_pixels[0])
    x_offset = x_ref_values[0] - x_scale * x_ref_pixels[0]
    y_scale = (y_ref_values[1] - y_ref_values[0]) / (y_ref_pixels[1] - y_ref_pixels[0])
    y_offset = y_ref_values[0] - y_scale * y_ref_pixels[0]
    x_data = x_scale * x_pixel + x_offset
    y_data = y_scale * y_pixel + y_offset
    return x_data, y_data

def extract_and_save_scaled_points(img_path, num_points, output_csv):
    print("First, select reference points for scaling.")
    x_ref_pixels, x_ref_values, y_ref_pixels, y_ref_values = get_scaling_parameters(img_path)
    print("Now, select the data points you want to extract.")
    img = plt.imread(img_path)
    plt.imshow(img)
    plt.title('Click on the data points you want to record\nClose the window after selecting points')
    points = plt.ginput(num_points, timeout=0)
    plt.close()
    scaled_points = [pixel_to_data(x, y, x_ref_pixels, x_ref_values, y_ref_pixels, y_ref_values) for x, y in points]
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['x', 'y'])
        writer.writerows(scaled_points)
    print(f"{len(points)} points extracted and saved to '{output_csv}' (scaled values)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract scaled points from an image and save to CSV.")
    parser.add_argument('--img', type=str, required=True, help="Image file path")
    parser.add_argument('--num', type=int, default=25, help="Number of points to extract")
    parser.add_argument('--out', type=str, default="extracted_points.csv", help="Output CSV filename")
    args = parser.parse_args()
    extract_and_save_scaled_points(args.img, args.num, args.out)
