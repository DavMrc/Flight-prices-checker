# Flight prices checker

## What I faced
Imagine this: you're browsing through flight offers for your next trip and, either by chance or aided by your favourite search engine, you realise that by extending your vacation by one day, you end up saving a lot of money on the flight ticket.

That happened to me more than a couple of times and, being a low-budget traveller, the flight ticket usually takes from 30% up to 60% of my total travel expenses. Usually I'm more than happy to extend my vacation by a couple of days if that saves money.

Unfortunately, no search engine is this flexible at present times. Most you can do is select a window of X days of vacation and see that in three days that same window of X days costs less.

## What I *really* wanted
"Very simply", I just wanted a way to browse through a period of, say, one month for those X to X+Y days that were the cheapest to fly.

Naturally, cheaper flights aren't always the most convenient. In the case of trips with layovers, it is quite common to find a flight offer that costs, say, 200€ but the total duration is double the time of another offer that costs maybe 300€.

That is why I also wanted to filter for total trip duration, which luckily is already built into most search engines.

## How I solved it
Thanks to [this library](https://github.com/krisukox/google-flights-api) I developed a couple of Go functions that I published on Google Cloud Platform under Cloud Functions.

In the published notebook, you can see a demo of the code to travel to Madeira, a magic, unreal island that stole my heart a while ago.

## Future improvements
- allow the selection of a city rather than an airport to depart from/land to
- localize the results (currency, airport names etc.)
- develop a visual interface to dynamically change the input parameters
- develop a visual interface to visualize the results