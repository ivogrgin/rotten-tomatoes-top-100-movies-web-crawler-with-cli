import requests
import lxml
import re
from bs4 import BeautifulSoup
import json
import argparse
import sys
import os


# Remove spaces (when there are 4 or more in a row) and newline character
def string_cleanup(text):
    return re.sub("\s{4,}", "", text).replace('\n', '')


def main(link, JSON_path, print_to_screen):
    headers = {'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'
                             ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127'
                             ' Mobile Safari/537.36'}
    r = requests.get(link, headers=headers)
    # get contents of page
    soup = BeautifulSoup(r.content, 'lxml')
    # find all a tags that contain the top movies
    links = soup.find_all('a', class_='unstyled articleLink')
    # list of
    movie_links = [link for link in links if '/m/' in link['href']]
    the100 = {}
    counter_to_100 = 1
    print(f"Data collection start! Collecting from {link}")

    # gets text for all movies
    for movie_link in movie_links:
        the100.update({string_cleanup(movie_link.text): {}})
        movie_r = requests.get('https://www.rottentomatoes.com' + movie_link['href'], headers=headers)
        soup_movie = BeautifulSoup(movie_r.content, 'lxml')
        # get movie description
        description = soup_movie.find('div', class_="movie_synopsis clamp clamp-6 js-clamp",
                                      id="movieSynopsis", style="clear:both")
        if description is None:
            print(f"Error on {counter_to_100}. Skipping...")
            # counter_to_100 += 1
            continue
        the100[string_cleanup(movie_link.text)] \
            .update({"Description": string_cleanup(description.text)})

        list_details = soup_movie.find('ul', class_="content-meta info")
        # get movie info

        for li in list_details.find_all('li'):
            counter = 0
            key = ''
            for div in li.find_all('div'):
                if len(li.find_all('div')) == 2:
                    if counter == 0:
                        key = div.text[:-1]
                        counter += 1
                    elif counter == 1:
                        the100[string_cleanup(movie_link.text)].update(
                            {key: re.sub("\xa0", " ", re.sub("\s{4,}", "", div.text)
                                         .replace('\n', ''))})

        the100[string_cleanup(movie_link.text)] \
            .update({"Cast & Crew": {}})
        cast_crew_section = soup_movie.find('section', id="movie-cast")
        cast_crew_section_div = cast_crew_section.find('div', class_="panel-body content_body")
        cast_crew_section_div_section = cast_crew_section_div.find('div', class_="castSection")
        cast_crew = cast_crew_section_div_section.find_all(lambda tag: tag.name == 'div')
        # add cast and crew and their roles
        for person_name_role in cast_crew:
            for person_name_role_div in person_name_role.find_all('div', class_="media-body"):
                count = 0
                person = ""
                for person_name_role_span in person_name_role_div.find_all('span'):

                    if count == 0:
                        if string_cleanup(person_name_role_span.text) not \
                                in the100[string_cleanup(movie_link.text)]["Cast & Crew"] \
                                .keys():
                            the100[string_cleanup(movie_link.text)]["Cast & Crew"].update(
                                {string_cleanup(person_name_role_span.text): []})
                        person = person_name_role_span.text
                    if count == 1:
                        the100[string_cleanup(movie_link.text)]["Cast & Crew"][
                            string_cleanup(person)]. \
                            append(string_cleanup(person_name_role_span.text))
                    count += 1
        print(f"{counter_to_100}/100")
        counter_to_100 += 1

    print(f"{counter_to_100}/100 Data collection completed!")

    if print_to_screen:
        print("Printing to screen")
        counter = 0
        title_printed = False
        print(the100.keys())
        for movie_names in the100.keys():
            print(f"{counter + 1}. {movie_names}")
            counter = counter + 1
            for key in the100[movie_names].keys():
                if type(the100[movie_names][key]) is not dict:
                    print("-" * len(f"{key}"))
                    print(f"{key}", end=": ")
                    print(the100[movie_names][key])
                elif not title_printed:
                    print("-" * len(f"{key}"))
                    print(f"{key.upper()}")
                    title_printed = True
                else:
                    print("-" * len(f"{key}"))
                    print(f"{key}", end=": ")
                    print(', '.join(map(str, the100[movie_names][key])))
                    print("\n")

    if JSON_path is not None:

        if sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
            print(f"saving JSON to: {JSON_path}\\top100.json")
            with open(JSON_path + "\\top100.json", 'w') as file:
                file.write(json.dumps(the100, indent=4))
        else:
            print(f"saving JSON to: {JSON_path}/top100.json")
            with open(JSON_path + "/top100.json", 'w') as file:
                file.write(json.dumps(the100, indent=4))

    print("All Done!")


if __name__ == "__main__":
    safe_start = True
    parser = argparse.ArgumentParser(description="rotten tomatoes TOP100 movies we crawler")
    parser.add_argument("-l", required=False, dest="link", type=str,
                        default="https://www.rottentomatoes.com/top/bestofrt/",
                        help="link to a rotten tomatoes TOP100 movies list.\n"
                             "USAGE: -l link\n"
                             "DEFAULT: https://www.rottentomatoes.com/top/bestofrt/")
    parser.add_argument("-s", required=False, dest="JSON_path", type=str,
                        help="Save data as JSON.\n"
                             "USAGE: -s [path] \n"
                             "DEFAULT: file will not be saved to json file")
    parser.add_argument("-p", required=False, action=argparse.BooleanOptionalAction, dest="print_to_screen", type=bool,
                        default=False,
                        help="Print data to screen in JSON format.\n"
                             "USAGE: -p\n"
                             "DEFAULT: text will not be printed\n")
    args = parser.parse_args()
    if not os.path.exists(args.JSON_path):
        print(f"file path is invalid or incorrect. {args.JSON_path}")
        safe_start = False
    if "https://www.rottentomatoes.com" not in args.link:
        print("link has to be to https://www.rottentomatoes.com")
        safe_start = False
    if args.link[-1] != "/" and safe_start:
        main(args.link + "/", args.JSON_path, args.print_to_screen)
    elif safe_start:
        main(args.link, args.JSON_path, args.print_to_screen)
