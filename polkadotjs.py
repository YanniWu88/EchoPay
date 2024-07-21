import tkinter as tk
from tkinter import messagebox
import speech_recognition as sr
import spacy
from substrateinterface import SubstrateInterface
from substrateinterface.base import Keypair  # Adjusted import path

class VoicePaymentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Polkadot Voice Payment")

        self.label = tk.Label(root, text="Click the button and say or type your transaction details.")
        self.label.pack(pady=10)

        self.capture_button = tk.Button(root, text="Capture Speech", command=self.capture_speech)
        self.capture_button.pack(pady=10)

        self.manual_entry_label = tk.Label(root, text="Or enter details manually (e.g., 'Send 5 DOT to Alice'):")
        self.manual_entry_label.pack(pady=10)

        self.manual_entry = tk.Entry(root, width=50)
        self.manual_entry.pack(pady=10)

        self.submit_button = tk.Button(root, text="Submit", command=self.manual_input)
        self.submit_button.pack(pady=10)

        self.result_label = tk.Label(root, text="")
        self.result_label.pack(pady=10)

        self.confirm_button = tk.Button(root, text="Confirm Transaction", command=self.confirm_transaction)
        self.confirm_button.pack(pady=10)
        self.confirm_button.config(state=tk.DISABLED)

        self.nlp = spacy.load("en_core_web_sm")
        self.amount = None
        self.recipient = None

    def capture_speech(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.label.config(text="Listening...")
            print("Listening...")
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            self.result_label.config(text=f"You said: {text}")
            print(f"You said: {text}")
            self.parse_transaction_details(text)
except sr.UnknownValueError:
            self.result_label.config(text="Sorry, I did not understand that.")
            print("Sorry, I did not understand that.")
        except sr.RequestError as e:
            self.result_label.config(text=f"Could not request results from Google Speech Recognition service; {e}")
            print(f"Could not request results from Google Speech Recognition service; {e}")

    def manual_input(self):
        text = self.manual_entry.get()
        self.result_label.config(text=f"You entered: {text}")
        print(f"You entered: {text}")
        self.parse_transaction_details(text)

    def parse_transaction_details(self, text):
        doc = self.nlp(text)
        self.amount = None
        self.recipient = None

        for token in doc:
            if token.like_num:
                self.amount = float(token.text)
            elif token.pos_ == "PROPN":
                self.recipient = token.text

        if self.amount and self.recipient:
            self.result_label.config(text=f"Parsed Amount: {self.amount} DOT, Recipient: {self.recipient}")
            print(f"Parsed Amount: {self.amount} DOT, Recipient: {self.recipient}")
            self.confirm_button.config(state=tk.NORMAL)
        else:
            self.result_label.config(text="Could not parse transaction details.")
            print("Could not parse transaction details.")

    def confirm_transaction(self):
        if self.amount and self.recipient:
            response = messagebox.askyesno("Confirm Transaction", f"Do you want to send {self.amount} DOT to {self.recipient}?")
            if response:
                self.execute_transaction(self.amount, self.recipient)
            else:
                self.result_label.config(text="Transaction cancelled.")
                print("Transaction cancelled.")

    def execute_transaction(self, amount, recipient):
        try:
            # Try connecting to a different Polkadot node if the default one fails
            try:
                substrate = SubstrateInterface(url="wss://rpc.polkadot.io")
            except Exception as e:
                print(f"Failed to connect to rpc.polkadot.io: {e}")
                substrate = SubstrateInterface(url="wss://westend-rpc.polkadot.io")  # Alternative node
# Generate a keypair from the mnemonic
            keypair = Keypair.create_from_mnemonic("valid twelve or twenty-four word mnemonic phrase here")

            # Validate the account by querying the balance
            account_info = substrate.query("System", "Account", [keypair.ss58_address])
            free_balance = account_info.value['data']['free']
            print(f"Account balance: {free_balance} Planck")

            if free_balance <= 0:
                raise ValueError("Insufficient balance to perform the transaction.")

            # Verify the Balances module and transfer function exist
            balances_module = substrate.get_metadata_module("Balances")
            if not any(func.name == "transfer" for func in balances_module.call_functions):
                raise ValueError("Call function 'Balances.transfer' not found")

            call = substrate.compose_call(
                call_module='Balances',
                call_function='transfer',
                call_params={
                    'dest': recipient,
                    'value': int(amount * 10**10)  # DOT has 10 decimal places
                }
            )

            extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)
            receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
            self.result_label.config(text=f"Transaction sent. Block hash: {receipt.block_hash}")
            print(f"Transaction sent. Block hash: {receipt.block_hash}")
        except Exception as e:
            self.result_label.config(text=f"Transaction failed: {e}")
            print(f"Transaction failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VoicePaymentApp(root)
    root.mainloop()