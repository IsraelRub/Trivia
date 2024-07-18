import json
import random
import argparse
from typing import Dict, List, Union


class Question:
    def __init__(self, question: str, options: Dict[str, str], correct_answer: str, category: str, difficulty: str):
        self.question = question
        self.original_options = options
        self.original_correct_answer = correct_answer
        self.category = category
        self.difficulty = difficulty

        # Shuffle the options to randomize their order
        shuffled_items = list(options.items())
        random.shuffle(shuffled_items)
        self.shuffled_options = dict(
            enumerate(dict(shuffled_items).values(), 1))

        # Find the correct answer in the shuffled options
        if correct_answer in options:
            correct_text = options[correct_answer]
        else:
            correct_text = correct_answer

        # Store the correct answer as the number corresponding to its position in shuffled options
        self.correct_answer = next(str(num) for num, text in self.shuffled_options.items()
                                   if text.lower() == correct_text.lower())

    def ask(self) -> bool:
        while True:
            print(f"\nCategory: {self.category}, Difficulty: {
                  self.difficulty}")
            print(self.question)
            for number, option in self.shuffled_options.items():
                print(f"\t{number}. {option}")
            user_answer = input(
                "\nEnter your answer (number or full text of the answer): ").strip()

            # Check if the answer is valid and correct
            if user_answer.isdigit() and int(user_answer) in self.shuffled_options:
                return user_answer == self.correct_answer
            elif user_answer.lower() in [option.lower() for option in self.shuffled_options.values()]:
                return self.shuffled_options[int(self.correct_answer)].lower() == user_answer.lower()
            elif user_answer.isdigit():
                print("\nInvalid number. Please enter a number between 1 and", len(
                    self.shuffled_options))
            else:
                print(
                    "\nInvalid answer. Please enter a valid number or the full text of your answer.")


class Player:
    def __init__(self, name: str):
        self.name = name
        self.score = 0

    def add_point(self) -> None:
        self.score += 1

    def get_score(self) -> int:
        return self.score


class TriviaGame:
    def __init__(self, json_file: str):
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Organize questions by category and difficulty for efficient access during the game
        self.questions: Dict[str, Dict[str, List[Question]]] = {}
        for q in data:
            new_question = Question(
                q['question'],
                q['options'],
                q['correct_answer'],
                q['category'],
                q['difficulty']
            )
            if q['category'] not in self.questions:
                self.questions[q['category']] = {
                    'easy': [], 'medium': [], 'hard': []}
            self.questions[q['category']][q['difficulty']].append(new_question)

        self.players: List[Player] = []

    def add_player(self, name: str) -> None:
        player = Player(name)
        self.players.append(player)

    def print_win(self) -> None:
        high_score = max(player.get_score() for player in self.players)
        winners = [
            player.name for player in self.players if player.get_score() == high_score]

        if len(winners) == 1:
            print(f"\nThe winner is: {winners[0]} with {high_score} points.")
        else:
            print(f"\nThe winners are: {', '.join(
                winners)} with {high_score} points.")

    def get_available_categories(self) -> List[str]:
        return list(self.questions.keys())

    def get_available_difficulties(self, category: str) -> List[str]:
        return list(self.questions[category].keys())

    def choose_option(self, player: Player, options: List[str], option_type: str) -> str:
        while True:
            print(f"\n{player.name}, choose a {option_type}:")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
            choice = input(f"Enter the number or name of your {
                           option_type} choice: ").strip()

            # Allow selection by number or full name of the option
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(options):
                    return options[index]
            else:
                for option in options:
                    if option.lower() == choice.lower():
                        return option

            print("Invalid choice. Please try again.")

    def choose_category(self, player: Player) -> str:
        available_categories = []
        for category, difficulties in self.questions.items():
            if any(difficulties.values()):
                available_categories.append(category)
        return self.choose_option(player, available_categories, "category")

    def choose_difficulty(self, player: Player, category: str) -> str:
        available_difficulties = []
        for difficulty, questions in self.questions[category].items():
            if questions:
                available_difficulties.append(difficulty)
        return self.choose_option(player, available_difficulties, "difficulty")

    def play(self) -> None:
        player_index = -1

        while True:
            # Check if there are any questions left in any category and difficulty
            if not any(questions for categories in self.questions.values() for questions in categories.values()):
                break

            player_index = (player_index + 1) % len(self.players)
            player = self.players[player_index]

            print("\n" + "=" * 30)
            print(f"\n{player.name}'s turn:")

            # Let the player choose category and difficulty
            available_categories = [
                cat for cat, difficulties in self.questions.items() if any(difficulties.values())]
            if not available_categories:
                break

            category = self.choose_option(
                player, available_categories, "category")
            available_difficulties = [
                diff for diff, questions in self.questions[category].items() if questions]
            if not available_difficulties:
                del self.questions[category]
                continue

            difficulty = self.choose_option(
                player, available_difficulties, "difficulty")

            if self.questions[category][difficulty]:
                question = random.choice(self.questions[category][difficulty])
                if question.ask():
                    print("\nCorrect!")
                    player.add_point()
                    self.questions[category][difficulty].remove(question)

                    # Remove empty difficulties and categories
                    if not self.questions[category][difficulty]:
                        del self.questions[category][difficulty]
                    if not self.questions[category]:
                        del self.questions[category]
                else:
                    print("\nIncorrect :-(")
            else:
                print(f"No more questions available in {
                      category} at {difficulty} difficulty.")

        print("\nGame over! Final scores:")

        self.print_win()

    def setup_players(self, num_players: int) -> None:
        for i in range(num_players):
            name = input(f"\nEnter name for player {i+1}: ")
            self.add_player(name)

    def from_arguments(args: argparse.Namespace) -> 'TriviaGame':
        game = TriviaGame(args.words_file)
        game.setup_players(args.num_players)
        return game


def validate_num_players(value: str) -> int:
    try:
        num = int(value)
        if num <= 0:
            raise argparse.ArgumentTypeError(
                "Number of players must be positive")
        return num
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Number of players must be an integer")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trivia game")
    parser.add_argument("words_file", type=str,
                        help="path to the file containing the questions")
    parser.add_argument(
        "num_players", type=validate_num_players, help="the number of players")
    args = parser.parse_args()

    game = TriviaGame.from_arguments(args)
    game.play()
