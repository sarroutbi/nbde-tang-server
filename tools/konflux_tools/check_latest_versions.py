""" This program receives a directory through --directory parameter (.tekton by default)
    and checks the different versions of the images for each of the tools in the directory.
    It then compares the versions with the latest versions available in Quay and prints
    the results or changes the versions in the pipelines directory if the --update flag is set.
    To check which is the current image, a line like the following should be present in the file:
    value: quay.io/konflux-ci/tekton-catalog/task-fbc-related-image-check:0.2@sha256:7a56...a6f
    By default, the program will check quay.io/konflux-ci/tekton-catalog/ as the pattern to check.
    If a different pattern is needed, it can be passed through the --pattern-line parameter.
    The program will check return the latest version in the container repository """
import argparse
import json
import subprocess
from os import listdir
from os.path import isfile, join

FILTER_LINE = "quay.io/konflux-ci/tekton-catalog/"

class Logger: # pylint: disable=too-few-public-methods
    """ Logger class """
    def __init__(self, verbose):
        self.verbose = verbose

    def vprint(self, *args, sep=" "):
        """ Print only if verbose is set """
        if self.verbose:
            print(*args, sep=sep)

def parse_arguments():
    """ Parse the arguments of the program """
    parser = argparse.ArgumentParser(
        description="Check the latest versions of the tools in the given directory")
    parser.add_argument("--directory", help=
                        "The directory to check the versions of the tools")
    parser.add_argument("--pattern", help=
                        "The pattern parameter to use to check the versions of the tools")
    parser.add_argument("--update",help=
                        "Update the versions of the tools in the pipelines directory",
                        action="store_true")
    parser.add_argument("--verbose", help=
                        "Print verbose output", action="store_true")
    return parser.parse_args()

class VersionChecker:
    """ Class to check the versions of the tools in the given directory """
    def __init__(self, input_args):
        """ Constructor """
        self.parsed_images = {}
        self.input_args = input_args
        self.logger = Logger(self.input_args.verbose)

    def read_files(self, directory):
        """ Read all files in directory and return a list with the files """
        onlyfiles = [(directory + "/" + f).strip() for f in listdir(directory)
                    if isfile(join(directory, f))]
        self.logger.vprint(onlyfiles)
        return onlyfiles

    def get_latest_tag_from_list(self, image, tags):
        """ Get the latest tag from a list of tags """
        most_recent_created = "2000-01-01T00:00:00.000000000Z"
        most_recent_tag = ""
        for tag in tags:
            result = subprocess.run(["skopeo", "inspect", "-n", "docker://" + image + ":" + tag],
                                    stdout=subprocess.PIPE, check=False)
            created = json.loads(result.stdout.decode("utf-8"))["Created"]
            self.logger.vprint("Tag:", tag, ", Created:", created, sep="")
            if created >= most_recent_created:
                most_recent_created = created
                most_recent_tag = tag
        self.logger.vprint("Most recent tag:", most_recent_tag)
        return most_recent_tag


    def get_digest_from_tag(self, image_with_tag):
        """ This function gets the digest of the latest tag """
        result = subprocess.run(["skopeo", "inspect", "-n", "docker://" + image_with_tag],
                                stdout=subprocess.PIPE, check=False)
        return json.loads(result.stdout.decode("utf-8"))["Digest"]

    def print_latest_tag(self, image):
        """ Get the latest tag of an image:
            This function extracts all the tags for a given image through skopeo
            and for each tag, it extracts the date and returns the more recent tag
        """
        if image in self.parsed_images:
            self.logger.vprint("WARNING: Already parsed image:", image)
            return
        result = subprocess.run(["skopeo", "list-tags", "docker://" + image],
                                stdout=subprocess.PIPE, check=False)
        self.logger.vprint("Result:", result.stdout.decode("utf-8"))
        tags = json.loads(result.stdout.decode("utf-8"))["Tags"]
        self.logger.vprint("Tags:", tags)
        # Get latest tag
        latest_tag = self.get_latest_tag_from_list(image, tags)
        digest = self.get_digest_from_tag(image + ":" + latest_tag)
        self.parsed_images[image] = True
        print("Latest tag with digest:->", image + ":" + latest_tag + "@" + digest, "<-")

    def print_latest_versions(self, file, pattern_filter=FILTER_LINE):
        """ Get the latest versions of the tools in the file """
        for line in file:
            if pattern_filter in line:
                # Remove the value: part by splitting the line from filter
                image = (pattern_filter + line.split(pattern_filter)[1]).strip(" ").rstrip(" ")
                non_sha_image = image.split("@")[0]
                non_tag_image = non_sha_image.split(":")[0]
                self.logger.vprint("Image:", image.strip().rstrip(), sep="")
                self.logger.vprint("No SHA Image:", non_sha_image, sep="")
                self.logger.vprint("No tag Image:", non_tag_image, sep="")
                self.print_latest_tag(non_tag_image)


    def check_versions(self):
        """ Read all files in directory """
        files = self.read_files(self.input_args.directory)
        for file in files:
            with open(file, encoding='utf-8') as f:
                if self.input_args.pattern:
                    self.print_latest_versions(f, self.input_args.pattern)
                else:
                    self.print_latest_versions(f)

def main():
    """ Main method """
    VersionChecker(parse_arguments()).check_versions()

if __name__ == "__main__":
    main()
