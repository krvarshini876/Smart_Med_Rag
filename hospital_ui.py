import webbrowser

def open_maps(search_query):
    url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
    print(f"\nOpening: {url}\n")   # debug
    webbrowser.open(url)


def hospital_menu():
    while True:   # 🔥 keeps program running
        print("\n🏥 FIND HEALTHCARE NEAR YOU\n")
        print("1. Hospitals")
        print("2. Clinics & Urgent Care")
        print("3. Pharmacies")
        print("4. Diagnostic Labs")
        print("5. Specialist Doctors")
        print("0. Exit\n")

        choice = input("Select option: ")

        if choice == "1":
            open_maps("emergency hospitals near me")

        elif choice == "2":
            open_maps("clinics near me")

        elif choice == "3":
            open_maps("pharmacy near me")

        elif choice == "4":
            open_maps("diagnostic labs near me")

        elif choice == "5":
            open_maps("specialist doctors near me")


        elif choice == "0":
            print("Exiting...")
            break

        else:
            print("Invalid choice")


if __name__ == "__main__":
    print("🚀 Starting Hospital Finder...\n")  # DEBUG LINE
    hospital_menu()