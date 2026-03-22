import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from agent import run_agent

print("Running Women AI Life-Load Assistant...")
print("-" * 50)

plan = run_agent()

print(f"Day Assessment: {plan['day_assessment']}\n")

print("Top Work Tasks:")
for t in plan["top_work_tasks"]:
    print(f"  - {t['task']}")

print("\nDeferred Tasks:")
for t in plan.get("deferred_work_tasks", []):
    print(f"  - {t['task']}")

print(f"\nDinner Tonight: {plan['dinner_suggestion']['name']} ({plan['dinner_suggestion']['prep_time_mins']} mins)")
print(f"Instructions: {plan['dinner_suggestion']['instructions']}")

print(f"\nGrocery List: {', '.join(plan['grocery_list'])}")
print(f"\nTime Saved: ~{plan['time_saved_mins']} minutes")
print(f"\n{plan['motivational_note']}")