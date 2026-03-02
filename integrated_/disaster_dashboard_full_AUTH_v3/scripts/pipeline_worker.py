import time
import traceback
from scripts.process_posts_to_db import process_batch

SLEEP_SECONDS = 5

def main():
    print("🚀 Pipeline Worker Started")
    print("Press CTRL+C to stop")

    while True:
        try:
            processed = process_batch(limit=20)

            if processed > 0:
                print(f"✅ Processed {processed} new posts")
            else:
                print("⏳ No new posts")

            time.sleep(SLEEP_SECONDS)

        except KeyboardInterrupt:
            print("\n🛑 Worker stopped manually")
            break

        except Exception as e:
            print("❌ Worker error:", str(e))
            traceback.print_exc()
            time.sleep(10)  # wait before retry

if __name__ == "__main__":
    main()