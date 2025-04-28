# UCI Search Engine Crawler

A web crawler designed to index UCI's School of Information and Computer Sciences (ICS) websites. This project is part of the UCI Search Engine project, focusing on the crawling component.

## Features

- **Targeted Crawling**: Focuses on UCI ICS-related websites (ics.uci.edu, cs.uci.edu, informatics.uci.edu, stat.uci.edu)
- **Smart Rate Limiting**: Domain-specific rate limiting to prevent server overload
- **Data Storage**: Tracks URL relationships, links, and crawling statistics
- **Error Handling**: Graceful handling of SSL/HTTP errors with retry logic
- **Real-time Monitoring**: Live statistics and error tracking

## System Logic & Data Flow

### 1. URL Processing
```
Start URL → Check Rate Limit → Fetch Content → Parse Links → Store Data → Update Stats
```
- Check if URL is completed/valid before processing
- Extract and filter links for ICS domains
- Add new URLs to frontier, mark current as complete

### 2. Rate Limiting
```
Request → Check Domain Limit → Wait if Needed → Process → Update Last Request Time
```
- Track last request time per domain
- Enforce 2-second delay between requests
- Prevent overwhelming any single domain

### 3. Data Management
```
Crawl URL → Store Data → Extract Links → Create Relationships → Update Statistics
```
- Store URL metadata and relationships
- Track domain-specific statistics
- Monitor overall crawling progress

## Future Improvements

- Implement multithreading for parallel crawling
- Add content indexing and search functionality
- Develop frontend interface
- Add more robust error handling and recovery
- Implement distributed crawling
