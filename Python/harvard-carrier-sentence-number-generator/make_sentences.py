#!/usr/bin/env python3

import random
import argparse

def main(NUM_TURNS=100, seed=24) -> None:
    path_to_sentences = './sentences_list.txt'
    
    # open and read lines into list
    with open(path_to_sentences, "r") as f:
        sentences = f.readlines()

    # randomizer
    random.seed(seed)
    for i in range(0, NUM_TURNS):
        with open("./formatted_sentences.txt", "a") as f: # open csv file in append mode
            sentence = sentences[random.randint(0, len(sentences)-1)] # select random sentence
            num = random.randint(0, 1000) # random number
            f.write(
                sentence.replace("_", str(num)) 
            ) # replace number in empty slot of sentence

if __name__ == "__main__":
    # argparser
    parser = argparse.ArgumentParser(
        prog='make-sentences-for-game',
        description='Makes sentences containing a random number from the modified' + \
            ' Harvard Sentences list.'
    )
    parser.add_argument(
        "turns", default=100, type=int, nargs='?',
        help='number of turns in the game'
    )
    parser.add_argument(
        '--seed', default=24, type=int, nargs='?',
        help='seed for random number generator.'
    )
    args = parser.parse_args()

    main(NUM_TURNS=args.turns, seed=args.seed) # call main function
