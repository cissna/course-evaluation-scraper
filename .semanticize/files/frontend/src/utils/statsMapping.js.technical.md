**Implementation Logic:**
1. Maps over `ALL_STAT_KEYS`.
2. For each `key`, it creates an array pair `[key, STATISTICS_CONFIG[key].defaultEnabled]`.
3. Uses `Object.fromEntries` to convert this array of pairs back into the desired state object format.