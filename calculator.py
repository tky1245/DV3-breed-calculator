
from dataclasses import dataclass
import pandas as pd
from typing import List, Any, Tuple

live_limited_dragons = ['Paruparu']
rate_up_dragons = ['Hell', 'Toddletomtom']

@dataclass
class Dragon:
    name: str
    hatch_time: float
    chance_category: str | None
    types: List[str]
    type_req: int | None
    limited: bool | None
    breedable: bool
    can_used_to_breed: bool


# Load spreadsheet
raw_df = pd.read_excel("DV3_breed data.xlsx", header=0)
raw_df.columns = (
    raw_df.columns.astype(str)
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
)

# If the first row repeats the header row, drop it.
first_row = raw_df.iloc[0].astype(str).str.strip().tolist()
if first_row == raw_df.columns.tolist():
    raw_df = raw_df.iloc[1:]

df = raw_df.reset_index(drop=True)

expected_columns = [
    "Dragon",
    "Time (hrs)",
    "Chance Category",
    "Type req",
    "Limited",
    "Breedable",
    "Can used to breed",
]

missing_columns = [col for col in expected_columns if col not in df.columns]
if missing_columns:
    raise KeyError(
        f"Missing expected spreadsheet columns: {missing_columns}. "
        f"Found columns: {df.columns.tolist()}"
    )

type_columns = [
    "Fire", "Water", "Wind", "Steel",
    "Earth", "Electric", "Light", "Dark",
    "Dream", "Soul"
]

dragons = []

for row_index, row in df.iterrows():
    dragon_types = [
        t for t in type_columns
        if t in df.columns and pd.notna(row[t]) and row[t] == 1
    ]

    dragon = Dragon(
        name=str(row["Dragon"]).strip(),
        hatch_time=float(row["Time (hrs)"]),
        chance_category=None if pd.isna(row["Chance Category"]) else str(row["Chance Category"]).strip(),
        types=dragon_types,
        type_req=None if pd.isna(row["Type req"]) else int(row["Type req"]),
        limited=False if pd.isna(row["Limited"]) else True,
        breedable=str(row["Breedable"]).strip().lower() == "yes",
        can_used_to_breed=str(row["Can used to breed"]).strip().lower() == "yes"
    )

    dragons.append(dragon)

# Fetch dragon by name
def get_dragon_by_name(name: str) -> Dragon | None:
    for dragon in dragons:
        if dragon.name.lower() == name.lower():
            return dragon
    return None

# Convert hours to time string
def hours_to_time_string(hours: float) -> str:
    total_seconds = int(hours * 3600)
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_parts = []
    if days > 0:
        time_parts.append(f"{days}d")
    if hours > 0:
        time_parts.append(f"{hours}h")
    if minutes > 0:
        time_parts.append(f"{minutes}m")
    if seconds > 0:
        time_parts.append(f"{seconds}s")
    return " ".join(time_parts) if time_parts else "0s"

# Calculation
class BreedResult:
    def __init__(self, dragon1: Dragon, dragon2: Dragon):
        self.dragon1 = dragon1
        self.dragon2 = dragon2
        self.resulting_dragons = self.calculate_resulting_dragons()

    def calculate_resulting_dragons(self) -> List[Tuple[Dragon, float]]:
        # combine unique types from both parents
        resulting_dragons = []
        existing_types = list(set(self.dragon1.types) | set(self.dragon2.types))
        remaining_rate = 1.0  # Start with a total chance of 100%
        common_weight_pool = 0.0 
        rare_unit_count = 0
        very_rare_unit_count = 0
        epic_unit_count = 0
        legendary_unit_count = 0
        for dragon_baby in dragons:
            rate_multiplier = 1.5 if dragon_baby.name in rate_up_dragons else 1.0
            # Check if the dragon's types are a subset of the existing types
            if set(dragon_baby.types).issubset(existing_types):
                # Check if the dragon is breedable and can be used to breed
                if dragon_baby.breedable and self.dragon1.can_used_to_breed and self.dragon2.can_used_to_breed:
                    # Special condition checks
                    if dragon_baby.type_req is not None and len(existing_types) < dragon_baby.type_req:
                        continue  # Skip if type requirement is not met
                    elif len(dragon_baby.types) > 2 and (len(self.dragon1.types) <= 1 or len(self.dragon2.types) <= 1):
                        continue  # Skip if the dragon has more than 2 types and either parent has 1 or fewer types
                    if dragon_baby.limited and (dragon_baby.name not in live_limited_dragons):
                        continue  # Skip if the dragon is limited and not in the live limited list


                    match dragon_baby.chance_category:
                        case "Common+":
                            common_weight_pool += 43.0 * rate_multiplier
                        case "Common-":
                            common_weight_pool += 37.0 * rate_multiplier
                        case "Rare": # 5% default
                            rare_unit_count += 1
                            remaining_rate -= 0.05 * 0.5 if dragon_baby.name in rate_up_dragons else 0
                        case "Very Rare": # 3% default
                            very_rare_unit_count += 1
                            remaining_rate -= 0.03 * 0.5 if dragon_baby.name in rate_up_dragons else 0
                        case "Epic": # 1.5% default
                            epic_unit_count += 1
                            remaining_rate -= 0.015 * 0.5 if dragon_baby.name in rate_up_dragons else 0
                        case "Legendary": # 0.75% default
                            legendary_unit_count += 1
                            remaining_rate -= 0.0075 * 0.5 if dragon_baby.name in rate_up_dragons else 0
        remaining_rate -= 0.1 if rare_unit_count > 1 else (0.05 if rare_unit_count > 0 else 0.0)
        remaining_rate -= 0.06 if very_rare_unit_count > 1 else (0.03 if very_rare_unit_count > 0 else 0.0)
        remaining_rate -= 0.03 if epic_unit_count > 1 else (0.015 if epic_unit_count > 0 else 0.0)
        remaining_rate -= 0.015 if legendary_unit_count > 1 else (0.0075 if legendary_unit_count > 0 else 0.0)

        # Chance calculation for resulting dragons
        for dragon_baby in dragons:
            if set(dragon_baby.types).issubset(existing_types) and dragon_baby.breedable and self.dragon1.can_used_to_breed and self.dragon2.can_used_to_breed:
                # Special condition checks
                if dragon_baby.type_req is not None and len(existing_types) < dragon_baby.type_req:
                    continue  # Skip if type requirement is not met
                elif len(dragon_baby.types) > 2 and (len(self.dragon1.types) <= 1 or len(self.dragon2.types) <= 1):
                    continue  # Skip if the dragon has more than 2 types and either parent has 1 or fewer types
                if dragon_baby.limited and (dragon_baby.name not in live_limited_dragons):
                    continue  # Skip if the dragon is limited and not in the live limited list

                
                chance = 0.0
                if dragon_baby.chance_category in ["Common+", "Common-"]:
                    chance = remaining_rate * (43.0 if dragon_baby.chance_category == "Common+" else 37.0) / common_weight_pool * rate_multiplier
                elif dragon_baby.chance_category == "Rare":
                    if rare_unit_count > 1:
                        chance = 0.1 / rare_unit_count
                    elif rare_unit_count > 0:
                        chance = 0.05 * rate_multiplier
                    if dragon_baby.name in rate_up_dragons:
                        chance += 0.1 * 0.5
                elif dragon_baby.chance_category == "Very Rare":
                    if very_rare_unit_count > 1:
                        chance = 0.06 / very_rare_unit_count
                    elif very_rare_unit_count > 0:
                        chance = 0.03 * rate_multiplier
                    if dragon_baby.name in rate_up_dragons:
                        chance += 0.03 * 0.5
                elif dragon_baby.chance_category == "Epic":
                    if epic_unit_count > 1:
                        chance = 0.03 / epic_unit_count
                    elif epic_unit_count > 0:
                        chance = 0.015 * rate_multiplier
                    if dragon_baby.name in rate_up_dragons:
                        chance += 0.015 * 0.5
                elif dragon_baby.chance_category == "Legendary":
                    if legendary_unit_count > 1:
                        chance = 0.015 / legendary_unit_count
                    elif legendary_unit_count > 0:
                        chance = 0.0075 * rate_multiplier
                    if dragon_baby.name in rate_up_dragons: 
                        chance += 0.0075 * 0.5
                resulting_dragons.append((dragon_baby, chance))
        return sorted(resulting_dragons, key=lambda x: x[1], reverse=False)  # Return the list of resulting dragons and their chances

    def average_hatch_time(self) -> float:
        if not self.resulting_dragons:
            return 0.0
        total_time = sum(dragon.hatch_time for dragon, _ in self.resulting_dragons)
        return total_time / len(self.resulting_dragons)
    
    def generate_breed_report(self) -> str: # generate an excel file of the breed result
        report_data = {
            "Dragon": [dragon.name for dragon, _ in self.resulting_dragons],
            "Chance": [f"{chance * 100:.2f}%" for _, chance in self.resulting_dragons], # Convert chance to percentage format
            "Hatch Time (hrs)": [hours_to_time_string(dragon.hatch_time) for dragon, _ in self.resulting_dragons],
            "Time (5% reduction) (hrs)": [hours_to_time_string(dragon.hatch_time * 0.95) for dragon, _ in self.resulting_dragons],
            "Time (8% reduction) (hrs)": [hours_to_time_string(dragon.hatch_time * 0.92) for dragon, _ in self.resulting_dragons],
            "Time (10% reduction) (hrs)": [hours_to_time_string(dragon.hatch_time * 0.9) for dragon, _ in self.resulting_dragons],
            "Types": [", ".join(dragon.types) for dragon, _ in self.resulting_dragons],
        }
        report_df = pd.DataFrame(report_data)
        output_file = f"{self.dragon1.name}_{self.dragon2.name}_breed_report.xlsx"
        report_df.to_excel(output_file, index=False)
        return output_file
        


# Generates an excel file of possible breed combinations given a list of target dragons
def breed_for_targets(target_dragons: List[str]) -> None:
    breed_list = []
    for dragon_parent1 in dragons:
        for dragon_parent2 in dragons[dragons.index(dragon_parent1):]:  # Avoid duplicate pairs and self-breeding
            breed_result = BreedResult(dragon_parent1, dragon_parent2)
            # Check if all target dragons are in the resulting dragons
            if all(any(result_dragon.name == target for result_dragon, _ in breed_result.resulting_dragons) for target in target_dragons):
                breed_list.append({
                    "Parent 1": dragon_parent1.name,
                    "Parent 2": dragon_parent2.name,
                    "Existing Types": list(set(dragon_parent1.types) | set(dragon_parent2.types)),
                    "Average Hatch Time": breed_result.average_hatch_time(),
                    "Average Speedup Cost": breed_result.average_hatch_time() * 120,
                })
    # Create a DataFrame and save to Excel
    breed_df = pd.DataFrame(breed_list)
    output_target = "target_breeding.xlsx"
    breed_df.to_excel(output_target, index=False)
            
# Interactive menu
def main():
    print("Welcome to the Dragon Breed Calculator!\n")
    while True:
        print("1. Calculate breed results for two dragons\n" \
        "2. Generate breed combinations for target dragons\n" \
        "3. Change limited and rate up dragon lists\n" \
        "4. Exit")
        choice = input("Please enter your choice (1-4): ")
        if choice == "1":
            dragon_name1 = input("Enter the name of the first dragon: ")
            dragon_name2 = input("Enter the name of the second dragon: ")
            dragon1 = get_dragon_by_name(dragon_name1)
            dragon2 = get_dragon_by_name(dragon_name2)
            if not dragon1 or not dragon2:
                print("One or both dragon names are invalid. Please try again.\n")
                continue
            if not dragon1.breedable or not dragon2.breedable:
                print("One or both dragons cannot be used for breeding. Please try again with different dragons.\n")
                continue
            breed_result = BreedResult(dragon1, dragon2)
            print(f"\nBreeding {breed_result.dragon1.name} and {breed_result.dragon2.name} can result in:")
            for dragon, chance in breed_result.resulting_dragons:
                print(f"- {dragon.name} with a chance of {chance:.2%}")
            report_choice = input("Do you want to generate a detailed breed report in Excel? (Y/N): ")
            if report_choice.upper() == "Y":
                report_file = breed_result.generate_breed_report()
                print(f"Detailed breed report generated and saved to {report_file}\n")
            else:
                print()
        elif choice == "2":
            target_dragons_input = input("Enter the names of target dragons separated by commas: ")
            target_dragons = [name.strip() for name in target_dragons_input.split(",")]
            breed_for_targets(target_dragons)
            print("Breed combinations have been generated and saved to target_breeding.xlsx\n")
        elif choice == "3":
            print(f"Current live limited dragons: {', '.join(live_limited_dragons)}")
            print(f"Current rate up dragons: {', '.join(rate_up_dragons)}")
            print("1. Update live limited dragons")
            print("2. Update rate up dragons")
            print("3. Back to main menu")
            sub_choice = input("Please enter your choice (1-3): ")
            if sub_choice == "1":
                new_live_limited = input("Enter the names of live limited dragons separated by commas: ")
                live_limited_dragons.clear()
                live_limited_dragons.extend(name.strip() for name in new_live_limited.split(","))
                print("Live limited dragons updated.\n")
            elif sub_choice == "2":
                new_rate_up = input("Enter the names of rate up dragons separated by commas: ")
                rate_up_dragons.clear()
                rate_up_dragons.extend(name.strip() for name in new_rate_up.split(","))
                print("Rate up dragons updated.\n")
            elif sub_choice == "3":
                continue
            else:
                print("Invalid choice. Please enter a number between 1 and 3.\n")
        elif choice == "4":
            print("Thank you for using the Dragon Breed Calculator!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 4.\n")

main()