import json
import os
import glob
import pathlib
from skimage import img_as_uint, io
import tifffile as tf
from tqdm import tqdm
import re


# Specify the path to your JSON file
tif_folder = r"D:\__Data\20240110_Mike_tissue_4x\XYstack_HistopathologySlide_CAMM_Pancrea_361_50_1"

##TODO replace poslist.pos with the metadata file from the MM acq
file_path = r"D:\__Data\20240110_Mike_tissue_4x\PositionList.pos"

data_folder = pathlib.Path(tif_folder).parent
tif_strip_folder = data_folder.joinpath("strip_metadata")
if not os.path.exists(tif_strip_folder):
    os.mkdir(tif_strip_folder)


# r"D:\__Data\20240110_Mike_tissue_4x\strip_metadata"

# file_path = r"D:\__Data\20240116_Mike_tissue_tilefix\poslist.pos"
# tif_folder = r"D:\__Data\20240116_Mike_tissue_tilefix\CAMM_Pancrea_361_50_1"
# tif_strip_folder = r"D:\__Data\20240116_Mike_tissue_tilefix\strip_metadata"


# Read the JSON file
with open(file_path) as json_file:
    data = json.load(json_file)

# Access the coordinates in map > StagePositions > array
pos = data["map"]["StagePositions"]["array"]
label_list = {}
position_list = {}
for ix, position in enumerate(pos):
    position_list.update(
        {
            (position["GridCol"]["scalar"], position["GridRow"]["scalar"]): position[
                "DevicePositions"
            ]["array"][0]["Position_um"]["array"]
        }
    )
    label_list.update(
        {
            (position["GridCol"]["scalar"], position["GridRow"]["scalar"]): position[
                "Label"
            ]["scalar"]
        }
    )
    # if ix<3:
    #    print(position["GridCol"]["scalar"],
    #      position["GridRow"]["scalar"],
    #      position["Label"]["scalar"],
    #      position["DevicePositions"]["array"][0]["Position_um"]["array"])

    # break
    # Print the coordinates
    # print(x,y)
# print(position_list)


save_config = True
save_tif = True

fl = glob.glob(tif_folder + r"\*.tif")

if save_config:
    # position_list = np.array(position_list)
    pixel_size = 1.105
    # pixel_size = 1
    # with open(os.path.join(r"D:\__Data\20230110_Mike_tissue_4x", 'TileConfiguration.txt'), 'w') as text_file:
    with open(
        os.path.join(tif_strip_folder, "TileConfiguration.txt"),
        "w",
    ) as text_file:
        print("dim = 2", file=text_file)
        for pos in range(len(fl)):
            fn = pathlib.Path(fl[pos]).name
            # print(fn)
            xy = re.findall(r"Pos(\d{3})_(\d{3})", fn)
            xy = [(int(x), int(y)) for x, y in xy][0]
            # print(xy)
            # print(position_list[xy])
            x, y = position_list[xy]
            # x = int(position_list[pos, 0] / pixel_size)
            # y = int(position_list[pos, 1] / pixel_size)
            # print(pos,fl[pos])
            # print(x,y,label_list[xy])
            x = x / pixel_size
            y = y / pixel_size

            # break
            # print(f"{fn}; ; ({int(x)}, {int(y)})")
            # print("====")
            print(f"{fn}; ; ({int(x)}, {int(y)})", file=text_file)
            # if pos==2:
            #    break
    text_file.close()


stitch_folder = tif_strip_folder

""" this was wrong! forgot indexing was added on the MM file

 if save_tif:
    flip_y = False
    flip_x = False
    for ix, fn in enumerate(fl):
        if ix == 0:
            img = io.imread(fn)
            print(img.shape)
        img1 = img[ix, :, :, :]
        if flip_y:
            img1 = img1[::-1, :,:]
        if flip_x:
            img1 = img1[:, ::-1,:]
        nfn = os.path.join(stitch_folder, f"{pathlib.Path(fn).name}")
        print(pathlib.Path(fn).name, pathlib.Path(nfn).name)
        io.imsave(nfn, img_as_uint(img1.sum(-1)), check_contrast=False)
 """


def get_xy_from_MM_position(position):
    devpos = position["DevicePositions"]
    devpos_xy = [_ for _ in devpos if _["Device"].startswith("XYStage")]
    assert len(devpos_xy) == 1
    x, y = devpos_xy[0]["Position_um"]
    return (x, y)


if save_tif:
    fn = fl[0]
    img = tf.TiffFile(fn)
    # positions_on_mmfile_stack = []
    labels_on_mmfile_stack = []
    for position in img.micromanager_metadata["Summary"]["StagePositions"]:
        # positions_on_mmfile_stack.append(get_xy_from_MM_position(position))
        labels_on_mmfile_stack.append(position["Label"])
        # print(position['Label'], get_xy_from_MM_position(position))
    img = img.asarray()
    print(img.shape)
    # print(positions_on_mmfile_stack)
    flip_y = True
    flip_x = False
    for ix in tqdm(range(img.shape[0]), total=img.shape[0]):
        img1 = img[ix, :, :, :]
        if flip_y:
            img1 = img1[::-1, :, :]
        if flip_x:
            img1 = img1[:, ::-1, :]

        label = labels_on_mmfile_stack[ix][
            2:
        ]  # remove the image-sequence tag on label eg : '2-Pos001_000'
        fnx = fn.replace("Pos000_000.ome.tif", f"{label}.ome.tif")
        nfn = os.path.join(stitch_folder, f"{pathlib.Path(fnx).name}")
        # print(pathlib.Path(fn).name, pathlib.Path(nfn).name)
        io.imsave(nfn, img_as_uint(img1), check_contrast=False)
