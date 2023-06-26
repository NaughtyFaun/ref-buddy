import csv
import os.path
import time
from datetime import date

from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from Env import Env
from models.models_lump import Session, ImageMetadata, ImageDupe


class DupeSearcher:

    def __init__(self):
        self.img_cache = {}

    def search(self, paths):
        count_max = len(paths)
        count = 0

        start_time = time.time()  # sec
        end_time = time.time()
        lap_time = 0.2

        running_paths = paths[:]
        dupes = []
        for p in paths:
            start_time = time.time()

            # Example usage
            target_image_path = p
            running_paths.remove(p)

            threshold = 0.99
            count += 1
            progress = count / count_max

            time_left = lap_time * ((1.0 - progress) * 100)

            # print(f'{lap_time} = {end_time} - {start_time}')
            similar_images = self.find_similar_images(target_image_path, running_paths, threshold)
            target_id = DupeSearcher.id_from_thumb_path(target_image_path)
            print(
                f"\r{progress * 100:.2f}% ~({time_left:.0f} sec left) Similar Images for {target_id} ({len(similar_images)}):",
                end='')
            for image_path in similar_images:
                print(f'{target_id};{DupeSearcher.id_from_thumb_path(image_path)};')
                dupes.append([target_id, DupeSearcher.id_from_thumb_path(image_path)])
            end_time = time.time()
            lap_time = end_time - start_time

        return dupes

    def find_similar_images(self, target_image_path, image_paths, threshold):
        """Finds similar images to the target image from a list of image paths."""
        target_image = Image.open(target_image_path)

        width, height = target_image.size
        ratio = float(width) / height

        similar_images = []
        for image_path in image_paths:
            image = Image.open(image_path)
            width, height = image.size
            chk_ratio = float(width) / height
            if abs(ratio - chk_ratio) > 0.001:
                # print(f'diff ratio ({ratio:.2f}/{chk_ratio:.2f})')
                continue

            similarity = self.calculate_similarity(target_image, image, target_image_path, image_path)
            if similarity >= threshold:
                similar_images.append(image_path)
        return similar_images

    def calculate_similarity(self, image1, image2, path1, path2):
        """Calculates the cosine similarity between two image feature vectors."""
        image1_features = self.extract_features(image1) if not path1 in self.img_cache else self.img_cache[path1]
        image2_features = self.extract_features(image2) if not path2 in self.img_cache else self.img_cache[path2]

        if not path1 in self.img_cache:
            self.img_cache[path1] = image1_features
        if not path2 in self.img_cache:
            self.img_cache[path2] = image2_features

        similarity = cosine_similarity([image1_features], [image2_features])[0][0]
        return similarity

    def extract_features(self, image):
        """Extracts image features as a flattened numpy array."""
        # Convert image to grayscale
        image = image.convert('L')
        # Resize the image to a fixed size for feature extraction
        image = self.resize_image(image, (64,64))
        # Convert the image to a numpy array
        image_array = np.array(image, dtype=np.float32)
        # Flatten the image array
        image_vector = image_array.flatten()
        return image_vector

    def resize_image(self, image, size):
        """Resizes the image to the specified size."""
        # return image.resize(size)
        return image

    @staticmethod
    def id_from_thumb_path(path:str) -> int:
        return int(os.path.basename(path).replace('.jpg', ''))

    @staticmethod
    def remove_array_dups(array:[int]) -> [int]:
        """Removes duplicates from an array based on the 'image_id' field."""
        unique_ids = set()
        unique_array = []

        for element in array:
            if element not in unique_ids:
                unique_ids.add(element)
                unique_array.append(element)

        return unique_array

    @staticmethod
    def write_to_csv(path:str, data):
        """Writes data to a CSV file with the current date in the filename."""
        today = date.today()
        filename = os.path.join(path, f"dupes_{today}.csv")

        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        print(f"Data written to {filename} successfully.")


if __name__ == '__main__':

    files = [os.path.join(Env.TMP_PATH, f) for f in os.listdir(Env.TMP_PATH) if os.path.isfile(os.path.join(Env.TMP_PATH, f))]


    [print(f) for f in files]

    with open(files[0], 'r', newline='') as file:
        reader = csv.reader(file)
        ids = [list(map(lambda id: int(id), line)) for line in reader]

    [print(id) for id in ids[0:10]]

    s = Session()
    for pair in ids:
        s.merge(ImageDupe(image1=pair[0], image2=pair[1]))
    s.commit()
    s.close()
    pass
    # # search
    # s = Session()
    # imgs_pron = s.query(ImageMetadata)\
    #     .filter(ImageMetadata.study_type_id == 2)\
    #     .order_by(ImageMetadata.imported_at.desc()).all()
    # imgs_art = s.query(ImageMetadata)\
    #     .filter(ImageMetadata.study_type_id == 3)\
    #     .order_by(ImageMetadata.imported_at.desc()).all()
    # imgs_bits = s.query(ImageMetadata)\
    #     .filter(ImageMetadata.study_type_id == 4)\
    #     .order_by(ImageMetadata.imported_at.desc()).all()
    # imgs = imgs_pron + imgs_bits + imgs_art
    # imgs = DupeSearcher.remove_array_dups(imgs)
    # count_max = len(imgs)
    #
    # print(f'Searching for duplicates in {count_max} files! Let\'s goooooooooo!')
    #
    # paths = [os.path.join(Env.THUMB_PATH, str(im.image_id)+'.jpg') for im in imgs]
    #
    # # [print(p) for p in paths]
    #
    # search = DupeSearcher()
    #
    # dupes = search.search(paths)
    #
    # search.write_to_csv(Env.TMP_PATH, dupes)
    #
    # print(f"\nFound ({len(dupes)}) duplicates:")
    # for d in dupes:
    #     print(f'{d[0]};{d[1]};')