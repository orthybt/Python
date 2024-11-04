
class Main:
    def __init__(self):
        self.app = OrthyApp()

    def start(self):
        print("Starting the Orthy application...")
        self.app.run()

if __name__ == "__main__":
    app = Main()
    app.start()
