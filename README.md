# TKO Analytics

An advanced UFC analytics platform powered by AI that provides deep insights into fight statistics, predictions, and performance metrics.

## Demo
[![TKO Analytics Demo](https://img.youtube.com/vi/Kjz1sZM8h_8/0.jpg)](https://youtu.be/Kjz1sZM8h_8?si=fFio7Z72YxImEHm1)

Click the image above to watch the demo video!

## Features

### Data Analysis
- Comprehensive UFC fight database updated through November 2024
- Multi-table query support for complex statistical analysis
- Real-time data visualization using PandasAI
- Advanced fight outcome predictions using XGBoost ML models
- Historical fight statistics and performance metrics
- Betting odds analysis and probability calculations

### Interactive Interface
- Natural language query processing using GPT-4
- Conversational AI assistant for data exploration
- Dynamic visualization generation
- Interactive dashboard with configurable views
- Multi-table data exploration capabilities
- Context-aware follow-up questions

### Technical Capabilities
- SQL query optimization for complex multi-table analysis
- BCNF-normalized database structure
- Real-time data processing and visualization
- Machine learning integration for predictive analytics
- Scalable architecture supporting live data updates

## Database Schema

### Core Tables
- **Fighters**: FighterID (PK), Name
- **Fights**: FightID (PK), Date, Location, Winner, FinishDetails, FinishRound, FinishRoundTime, TotalFightTimeSecs, RedFighterID (FK), BlueFighterID (FK)
- **Odds**: OddsID (PK), FightID (FK), RedOdds, BlueOdds, RedExpectedValue, BlueExpectedValue, RedDecOdds, BlueDecOdds, RSubOdds, BSubOdds, RKOOdds, BKOOdds

## Technology Stack
- **Backend**: Python, SQLite
- **ML/AI**: XGBoost, GPT-4, LangChain
- **Data Analysis**: PandasAI
- **Visualization**: Custom plotting tools with multi-table support

## Future Development
- Real-time fight analytics pipeline
- Enhanced prediction models incorporating fighting styles
- Live prediction capabilities
- Interactive visualization improvements
- React-based frontend migration
- Personalized user dashboards

## Installation
Repository available at: https://github.com/jaysomp/database-sys

## Authors
- Jaydeep Sompalli
- Jeet Arora
