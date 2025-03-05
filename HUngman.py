import random

def choose_word():
    words = ["python", "hangman", "developer", "challenge", "programming", "artificial"]
    return random.choice(words)

def display_word(word, guessed_letters):
    return " ".join(letter if letter in guessed_letters else "_" for letter in word)

def hangman():
    word = choose_word()
    guessed_letters = set()
    attempts = 6  # Number of incorrect guesses allowed

    print("Welcome to Hangman!")
    
    while attempts > 0:
        print("\nWord: ", display_word(word, guessed_letters))
        print(f"Attempts left: {attempts}")
        guess = input("Guess a letter: ").lower()
        
        if guess in guessed_letters:
            print("You already guessed that letter.")
        elif guess in word:
            print("Good guess!")
            guessed_letters.add(guess)
        else:
            print("Wrong guess!")
            guessed_letters.add(guess)
            attempts -= 1
        
        if all(letter in guessed_letters for letter in word):
            print("\nCongratulations! You guessed the word:", word)
            break
    else:
        print("\nGame Over! The word was:", word)

if __name__ == "__main__":
    hangman()
