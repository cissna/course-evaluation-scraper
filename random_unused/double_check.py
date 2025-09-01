import sys

# The list of department codes you provided.
# Using a set for faster lookups.
DEPARTMENT_CODES = {
    "AS.001","AS.004","AS.010","AS.020","AS.030","AS.040","AS.050","AS.060","AS.061","AS.070","AS.080",
    "AS.100","AS.110","AS.130","AS.134","AS.136","AS.140","AS.145","AS.150","AS.171","AS.173","AS.180",
    "AS.190","AS.191","AS.192","AS.194","AS.196","AS.197","AS.200","AS.210","AS.217","AS.220","AS.225",
    "AS.230","AS.250","AS.270","AS.271","AS.280","AS.290","AS.300","AS.305","AS.310","AS.360","AS.361",
    "AS.362","AS.363","AS.371","AS.374","AS.376","AS.389","AS.410","AS.420","AS.425","AS.430","AS.440",
    "AS.450","AS.455","AS.460","AS.465","AS.470","AS.472","AS.475","AS.480","AS.485","AS.490","AS.491",
    "AS.492","AS.999",
    "EN.500","EN.501","EN.510","EN.515","EN.520","EN.525","EN.530","EN.535","EN.540","EN.545","EN.553",
    "EN.555","EN.560","EN.565","EN.570","EN.575","EN.580","EN.585","EN.595","EN.601","EN.605","EN.615",
    "EN.620","EN.625","EN.635","EN.645","EN.650","EN.655","EN.660","EN.661","EN.662","EN.663","EN.665",
    "EN.670","EN.675","EN.685","EN.695","EN.700","EN.705"
}

def find_unlisted_prefixes(filename="jhu_as_en_courses.txt"):
    """
    Reads a file of course codes, extracts their prefixes, and finds which
    ones are not in the predefined DEPARTMENT_CODES set.

    Args:
        filename (str): The name of the file to read course codes from.
    
    Returns:
        list: A sorted list of prefixes found in the file but not in
              DEPARTMENT_CODES. Returns None if the file cannot be read.
    """
    found_prefixes = set()
    
    try:
        with open(filename, 'r') as f:
            for line in f:
                # Remove any leading/trailing whitespace
                course_code = line.strip()
                if not course_code:
                    continue
                
                # Split the code by '.' and take the first two parts
                parts = course_code.split('.')
                if len(parts) >= 2:
                    prefix = f"{parts[0]}.{parts[1]}"
                    found_prefixes.add(prefix)

    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        print("Please make sure it is in the same directory as this script.")
        return None
        
    # Use set difference to find prefixes that are in the file but not in our list
    unlisted_prefixes = found_prefixes.difference(DEPARTMENT_CODES)
    
    # Return a sorted list for consistent and readable output
    return sorted(list(unlisted_prefixes))

def main():
    """
    Main function to execute the script and print the results.
    """
    missing_prefixes = find_unlisted_prefixes()
    
    # If find_unlisted_prefixes returned None, it means there was an error.
    if missing_prefixes is None:
        sys.exit(1) # Exit with an error code

    if missing_prefixes:
        print("Found the following prefixes in the file that are NOT in your list:")
        for prefix in missing_prefixes:
            print(prefix)
    else:
        print("Success! All course prefixes found in the file exist in your DEPARTMENT_CODES list.")

if __name__ == "__main__":
    main()

