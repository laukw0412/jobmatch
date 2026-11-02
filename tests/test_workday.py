
import requests
import trafilatura


def main():
    url = (
        "https://sonyglobal.wd1.myworkdayjobs.com/"
        "wday/cxs/sonyglobal/SonyJapanCareers/"
        "job/Tokyo---Osaki/"
        "Full-Time---AI-Application-Engineer_JR-116505"
    )

    response = requests.get(
        url,
        headers={
            "User-Agent": "JobMatch/0.1",
            "Accept": "application/json",
        },
        timeout=15,
        allow_redirects=False,
    )

    print("Status Code:", response.status_code)
    print("Content Type:", response.headers.get("Content-Type"))

    response.raise_for_status()

    data = response.json()
    job = data.get("jobPostingInfo", {})

    print("\nJob Title:", job.get("title"))
    print("Location:", job.get("location"))

    description_html = job.get("jobDescription", "")

    text = trafilatura.extract(
        description_html,
        favor_recall=True,
        include_tables=True,
    )

    print("\n=== Job Description ===\n")
    print(text or "No description extracted.")


if __name__ == "__main__":
    main()
