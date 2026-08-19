from jobmatch.profile.loader import load_profile

def main():
    profile = load_profile("data/profile/profile.json")
    print("--------------------------------------")
    print(profile)

if __name__ == "__main__":
    main()