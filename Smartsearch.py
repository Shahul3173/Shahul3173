import json
import os
import tkinter as tk
from tkinter import ttk

class TrieNode:
    def __init__(self, char=""):
        self.char = char
        self.children = {}
        self.is_end_of_word = False
        self.frequency = 0

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word, frequency=1):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode(char)
            node = node.children[char]
        node.is_end_of_word = True
        node.frequency = frequency

    def search_prefix(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node
    
    def collect_words(self, node, prefix):
        results = []
        if node.is_end_of_word:
            results.append((prefix, node.frequency))
        for child in node.children.values():
            results.extend(self.collect_words(child, prefix + child.char))
        return results
    
    def autocomplete(self, prefix):
        node = self.search_prefix(prefix)
        if not node:
            return []
        words = self.collect_words(node, prefix)
        words.sort(key=lambda x: -x[1])
        return [word for word, freq in words]
    
    def select_word(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        if node.is_end_of_word:
            node.frequency += 1
            return True
        return False

def levenshtein_distance(a, b):
    if len(a) < len(b):
        a, b = b, a
    previous_row = list(range(len(b) + 1))
    for i, char_a in enumerate(a, 1):
        current_row = [i]
        for j, char_b in enumerate(b, 1):
            insertions = previous_row[j] + 1
            deletions = current_row[j - 1] + 1
            substitutions = previous_row[j - 1] + (char_a != char_b)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

class SmartTrie(Trie):
    def fuzzy_autocomplete(self, typo_prefix, max_distance=1):
        first_char = typo_prefix[0] if typo_prefix else ""
        all_words = self.collect_words(self.root, "")
        close_words = []
        for word, freq in all_words:
            if word.startswith(first_char) and levenshtein_distance(typo_prefix, word[:len(typo_prefix)]) <= max_distance:
                close_words.append((word, freq))
        close_words.sort(key=lambda x: -x[1])
        return [word for word, freq in close_words]

class SmartSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Search Bar")
        
        self.trie = SmartTrie()
        self.data_file = "word_frequencies.json"
        
        self.input_var = tk.StringVar()
        self.input_var.trace("w", self.update_suggestions)
        
        self.create_widgets()
        self.load_words()

    def load_words(self):
        # Default words if no file exists
        default_words = {
            "bear": 5, "bell": 2, "bid": 8, "buy": 10,
            "car": 7, "care": 3, "camp": 1, "can": 4,
            "camera": 6, "cancel": 2, "butter": 3
        }
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    word_freqs = json.load(f)
                    print("📂 Loaded word frequencies from file.")
            except json.JSONDecodeError:
                print("⚠️ Error reading save file. Using default words.")
                word_freqs = default_words
        else:
            word_freqs = default_words
            print("🆕 No save file found. Loaded default words.")
        
        for word, freq in word_freqs.items():
            self.trie.insert(word, freq)

    def save_words(self):
        all_words = self.trie.collect_words(self.trie.root, "")
        word_freqs = {word: freq for word, freq in all_words}
        
        with open(self.data_file, "w") as f:
            json.dump(word_freqs, f)
        print("💾 Saved word frequencies to file!")

    def create_widgets(self):
        self.entry = ttk.Entry(self.root, textvariable=self.input_var, width=40)
        self.entry.grid(row=0, column=0, padx=10, pady=10)

        self.listbox = tk.Listbox(self.root, width=40)
        self.listbox.grid(row=1, column=0, padx=10, pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.select_suggestion)

    def update_suggestions(self, *args):
        query = self.input_var.get().lower()
        if not query:
            self.listbox.delete(0, tk.END)
            return
        
        suggestions = self.trie.autocomplete(query)
        if not suggestions:
            suggestions = self.trie.fuzzy_autocomplete(query)

        self.listbox.delete(0, tk.END)
        for word in suggestions[:5]:  # Limit to top 5
            self.listbox.insert(tk.END, word)

    def select_suggestion(self, event):
        if not self.listbox.curselection():
            return
        index = self.listbox.curselection()[0]
        selected_word = self.listbox.get(index)
        self.input_var.set(selected_word)
        self.trie.select_word(selected_word)
        print(f"✅ Selected '{selected_word}', system learned!")
        self.save_words()  # Save immediately after learning!

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartSearchApp(root)  
    root.mainloop()
