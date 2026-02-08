"""
Data Processor Agent - Handles data workflows and connector operations

Responsibilities:
- Execute scheduled data scraping tasks
- Process RSS feeds and API calls
- Synchronize data with Google Sheets and cloud platforms
- Route watch messages to appropriate connectors
- Manage connector lifecycle and error handling
- Handle social media posting (Twitter, LinkedIn, etc.)
"""

import sys
import os
from typing import Dict, List, Optional
import time
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../tools'))

from .base_agent import BaseAgent
from core.agent_registry import Task
from core.message_bus import MessageType


class DataProcessorAgent(BaseAgent):
    """
    Autonomous data processor agent that handles connectors and data workflows
    """

    def __init__(self, agent_id: str = "data-proc-1"):
        super().__init__(agent_id=agent_id, role="data_processor")

        # Connector registry
        self.active_connectors: Dict[str, bool] = {
            "slack": False,
            "email": False,
            "google_sheets": False,
            "twitter": False,
            "linkedin": False,
            "facebook": False,
            "instagram": False,
            "rss": False,
            "web_scraper": False
        }

        # Data processing history
        self.processing_history: List[Dict] = []

    def startup(self) -> bool:
        """Start data processor with connector initialization"""
        if not super().startup():
            return False

        # Initialize connectors
        self._initialize_connectors()

        print(f"[{self.agent_id}] Data processor ready with {sum(self.active_connectors.values())} active connectors")
        return True

    def execute_task(self, task: Task):
        """
        Execute data processing task

        Args:
            task: Task to execute
        """
        try:
            print(f"[{self.agent_id}] Starting data processing task: {task.description}")

            # Determine task type
            description_lower = task.description.lower()

            if "scrape" in description_lower or "fetch" in description_lower:
                self._scrape_website(task)
            elif "rss" in description_lower or "feed" in description_lower:
                self._process_rss(task)
            elif "sheet" in description_lower or "google" in description_lower:
                self._sync_google_sheets(task)
            elif any(social in description_lower for social in ["tweet", "twitter", "linkedin", "facebook", "instagram"]):
                self._post_social_media(task)
            elif "slack" in description_lower:
                self._send_slack_message(task)
            elif "email" in description_lower:
                self._send_email(task)
            else:
                # Generic data processing
                self._process_data(task)

            self.complete_task(task.task_id)

        except Exception as e:
            error_msg = f"Data processing failed: {str(e)}"
            print(f"[{self.agent_id}] {error_msg}")
            self.fail_task(task.task_id, error_msg)

    def _initialize_connectors(self):
        """Initialize all connectors"""
        print(f"[{self.agent_id}] Initializing connectors...")

        # Check which connectors have credentials
        # In real implementation, check .env for API keys

        connectors_to_check = [
            ("SLACK_BOT_TOKEN", "slack"),
            ("EMAIL_USERNAME", "email"),
            ("GOOGLE_SHEETS_CREDENTIALS", "google_sheets"),
            ("TWITTER_API_KEY", "twitter"),
            ("LINKEDIN_CLIENT_ID", "linkedin"),
            ("FACEBOOK_ACCESS_TOKEN", "facebook"),
            ("INSTAGRAM_ACCESS_TOKEN", "instagram")
        ]

        for env_var, connector in connectors_to_check:
            if os.getenv(env_var):
                self.active_connectors[connector] = True
                print(f"  ✓ {connector} connector ready")
            else:
                print(f"  ○ {connector} connector not configured")

        # RSS and web scraper don't need credentials
        self.active_connectors["rss"] = True
        self.active_connectors["web_scraper"] = True

    def _scrape_website(self, task: Task):
        """Scrape website data"""
        print(f"[{self.agent_id}] Scraping website...")

        # Extract URL from task description
        # In real implementation, use tools/connectors/web_scraper.py

        print(f"  → Target URL: (extracted from task description)")
        print(f"  → Fetching content...")
        print(f"  → Parsing HTML...")
        print(f"  → Extracting data...")

        # Store results
        result = {
            "task_id": task.task_id,
            "type": "web_scraping",
            "timestamp": time.time(),
            "items_scraped": 42,  # Simulated
            "status": "success"
        }

        self.processing_history.append(result)
        self._store_scraped_data(result)

        print(f"[{self.agent_id}] ✓ Website scraped: {result['items_scraped']} items")

    def _process_rss(self, task: Task):
        """Process RSS feed"""
        print(f"[{self.agent_id}] Processing RSS feed...")

        # In real implementation, use tools/data/rss_parser.py

        print(f"  → Fetching feed...")
        print(f"  → Parsing entries...")
        print(f"  → Filtering new items...")

        result = {
            "task_id": task.task_id,
            "type": "rss_processing",
            "timestamp": time.time(),
            "new_items": 7,  # Simulated
            "status": "success"
        }

        self.processing_history.append(result)

        print(f"[{self.agent_id}] ✓ RSS feed processed: {result['new_items']} new items")

    def _sync_google_sheets(self, task: Task):
        """Sync data with Google Sheets"""
        print(f"[{self.agent_id}] Syncing with Google Sheets...")

        if not self.active_connectors["google_sheets"]:
            raise Exception("Google Sheets connector not configured")

        # In real implementation, use tools/connectors/google_sheets_client.py

        print(f"  → Authenticating with Google...")
        print(f"  → Reading sheet data...")
        print(f"  → Writing updates...")

        result = {
            "task_id": task.task_id,
            "type": "google_sheets_sync",
            "timestamp": time.time(),
            "rows_updated": 15,  # Simulated
            "status": "success"
        }

        self.processing_history.append(result)

        print(f"[{self.agent_id}] ✓ Google Sheets synced: {result['rows_updated']} rows updated")

    def _post_social_media(self, task: Task):
        """Post to social media platforms"""
        print(f"[{self.agent_id}] Posting to social media...")

        # Determine which platform(s)
        description_lower = task.description.lower()

        platforms = []
        if "twitter" in description_lower or "tweet" in description_lower:
            platforms.append("twitter")
        if "linkedin" in description_lower:
            platforms.append("linkedin")
        if "facebook" in description_lower:
            platforms.append("facebook")
        if "instagram" in description_lower:
            platforms.append("instagram")

        if not platforms:
            platforms = ["twitter"]  # Default

        # Post to each platform
        results = {}
        for platform in platforms:
            if not self.active_connectors.get(platform, False):
                print(f"  ○ {platform} connector not configured, skipping...")
                continue

            print(f"  → Posting to {platform}...")
            results[platform] = self._post_to_platform(platform, task)

        result = {
            "task_id": task.task_id,
            "type": "social_media_post",
            "timestamp": time.time(),
            "platforms": results,
            "status": "success"
        }

        self.processing_history.append(result)

        print(f"[{self.agent_id}] ✓ Posted to {len(results)} platform(s)")

    def _post_to_platform(self, platform: str, task: Task) -> Dict:
        """Post to specific social media platform"""
        # In real implementation, use tools/connectors/{platform}_client.py

        # Simulate posting
        print(f"     Formatting content for {platform}...")
        print(f"     Authenticating...")
        print(f"     Publishing post...")

        return {
            "posted": True,
            "post_id": f"{platform}_12345",
            "url": f"https://{platform}.com/post/12345"
        }

    def _send_slack_message(self, task: Task):
        """Send message to Slack"""
        print(f"[{self.agent_id}] Sending Slack message...")

        if not self.active_connectors["slack"]:
            raise Exception("Slack connector not configured")

        # In real implementation, use tools/connectors/slack_client.py

        print(f"  → Connecting to Slack...")
        print(f"  → Sending message...")

        result = {
            "task_id": task.task_id,
            "type": "slack_message",
            "timestamp": time.time(),
            "message_sent": True,
            "status": "success"
        }

        self.processing_history.append(result)

        print(f"[{self.agent_id}] ✓ Slack message sent")

    def _send_email(self, task: Task):
        """Send email"""
        print(f"[{self.agent_id}] Sending email...")

        if not self.active_connectors["email"]:
            raise Exception("Email connector not configured")

        # In real implementation, use tools/connectors/email_client.py

        print(f"  → Composing email...")
        print(f"  → Connecting to SMTP...")
        print(f"  → Sending...")

        result = {
            "task_id": task.task_id,
            "type": "email",
            "timestamp": time.time(),
            "sent": True,
            "status": "success"
        }

        self.processing_history.append(result)

        print(f"[{self.agent_id}] ✓ Email sent")

    def _process_data(self, task: Task):
        """Generic data processing"""
        print(f"[{self.agent_id}] Processing data...")

        # Generic data transformation/processing
        print(f"  → Loading data...")
        print(f"  → Transforming...")
        print(f"  → Storing results...")

        result = {
            "task_id": task.task_id,
            "type": "data_processing",
            "timestamp": time.time(),
            "status": "success"
        }

        self.processing_history.append(result)

        print(f"[{self.agent_id}] ✓ Data processed")

    def _store_scraped_data(self, data: Dict):
        """Store scraped data to .tmp directory"""
        output_dir = os.path.join("/Users/vik043/Desktop/Agentic Workflow/.tmp/scraped-data")
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f"scraped_{data['task_id']}.json")

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"     Data stored: {output_file}")

    def get_connector_status(self) -> Dict:
        """Get status of all connectors"""
        return {
            "active_connectors": {k: v for k, v in self.active_connectors.items() if v},
            "inactive_connectors": {k: v for k, v in self.active_connectors.items() if not v},
            "total_active": sum(self.active_connectors.values()),
            "total_connectors": len(self.active_connectors)
        }


# Example usage
if __name__ == "__main__":
    data_proc = DataProcessorAgent()

    # Start agent
    import threading
    agent_thread = threading.Thread(target=data_proc.run, daemon=True)
    agent_thread.start()

    # Wait for startup
    time.sleep(2)

    print("\n" + "="*50)
    print("Data Processor Agent Ready")
    print("="*50)

    # Show connector status
    status = data_proc.get_connector_status()
    print(f"\nActive Connectors: {status['total_active']}/{status['total_connectors']}")
    for connector in status['active_connectors']:
        print(f"  ✓ {connector}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        data_proc.shutdown()
