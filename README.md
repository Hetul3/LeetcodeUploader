# LeetCode Uploader

A automated CLI tool designed to sync your LeetCode solutions to a GitHub repository effortlessly.

## Overview

LeetCode Uploader is a utility that periodically or on-demand fetches your latest accepted submissions from LeetCode and commits them to a dedicated GitHub repository. It automates the process of maintaining a portfolio of your algorithmic solutions, complete with problem descriptions and organized folder structures.

## Key Features

- **Batch Sync**: Fetch and upload multiple recent solutions at once.
- **Automated Documentation**: Automatically creates a `README.md` for each problem using data from LeetCode.
- **Smart Organization**: Deposits solutions into structured folders based on problem names and difficulty.
- **Duplicate Detection**: Intelligently skips problems that have already been synced to your repository.
- **On-Demand Execution**: No need to keep it running constantly; just run it whenever you want to sync your latest work.

## How It Works

1. **Fetch**: Connects to the LeetCode GraphQL API to retrieve your recent accepted submissions.
2. **Verify**: Checks your GitHub repository to see which solutions are already present.
3. **Generate**: For each new solution, it fetches the problem description and formats it into a clean Markdown file.
4. **Push**: Uses the GitHub REST API to commit the solution and documentation files to your repository.

## Getting Started

Refer to `.env.example` for configuration details and `agents.md` for the technical specifications.