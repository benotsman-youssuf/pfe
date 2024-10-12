response = "What is an iPhone?\nAn iPhone is a series of smartphones created by Apple, running on the iOS operating system also developed by Apple.\n\nWho introduced the first iPhone?\nSteve Jobs unveiled the first iPhone, the iPhone 2G, on January 9, 2007.\n\nHow often does Apple release new iPhone models?\nApple releases new iPhone models and operating system updates every year.\n\nWhat is the estimated number of iPhones sold as of November 1, 2018?\nOver 2.2 billion iPhones have been sold as of November 1, 2018.\n\nWhat is the primary user interface feature of the iPhone?\nThe iPhone's user interface is based on a multi-touch screen. \n"

content = response.split('\n\n')

for card in content:
    pair = card.split('\n')
    question = pair[0]
    answer = pair[1]
    print(f"Question: {question}")
    print(f"Answer: {answer}")
    print("--------------------------------------")

