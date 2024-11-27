// RelayManager.js

const { group } = require("console");
const fs = require("fs");

const dataPath = "./data.json";
const backupPath = "./data-back.json";

const get_data = async () => {
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms)); // Helper for waiting

  try {
    const readDataFile = () => {
      const jsonData = fs.readFileSync(dataPath, "utf8");
      return JSON.parse(jsonData);
    };

    // Attempt initial read of data.json
    let parsedData = null;
    try {
      parsedData = readDataFile();
    } catch (err) {
      console.error("Error reading data.json on first attempt:", err);
    }

    // Check validity of initial read
    if (
      parsedData === null ||
      parsedData === undefined ||
      (typeof parsedData !== "object" && !Array.isArray(parsedData))
    ) {
      console.warn("data.json is invalid or empty. Retrying in 5 seconds...");
      await wait(5000); // Wait for 5 seconds

      // Retry reading data.json
      try {
        parsedData = readDataFile();
      } catch (err) {
        console.error("Error reading data.json on retry:", err);
      }

      // Validate data after retry
      if (
        parsedData === null ||
        parsedData === undefined ||
        (typeof parsedData !== "object" && !Array.isArray(parsedData))
      ) {
        console.warn(
          "data.json is still invalid or empty. Falling back to data-back.json..."
        );

        // Read data-back.json and restore data.json
        try {
          const backupData = fs.readFileSync(backupPath, "utf8");
          const parsedBackupData = JSON.parse(backupData);

          // Write backup data to data.json
          fs.writeFileSync(
            dataPath,
            JSON.stringify(parsedBackupData, null, 2),
            "utf8"
          );
          console.log("Restored data.json from data-back.json!");

          return parsedBackupData; // Return backup data
        } catch (err) {
          console.error("Error reading or restoring from data-back.json:", err);
          return null; // Return null if both fail
        }
      }
    }

    console.log("Data successfully read from data.json!");
    return parsedData; // Return valid data
  } catch (err) {
    console.error("Unexpected error:", err);
    return null; // Return null in case of unexpected error
  }
};

const set_data = (newData) => {
  console.log("Data Updating");

  if (newData === null || newData === undefined) {
    console.error(
      "Invalid data: newData is null or undefined. Aborting write."
    );
    return false;
  }

  try {
    // Read current content of data.json and data-back.json
    const currentData = fs.existsSync(dataPath)
      ? JSON.parse(fs.readFileSync(dataPath, "utf8"))
      : null;
    const backupData = fs.existsSync(backupPath)
      ? JSON.parse(fs.readFileSync(backupPath, "utf8"))
      : null;

    // Compare newData with the current data.json and data-back.json
    if (
      JSON.stringify(newData) === JSON.stringify(currentData) &&
      JSON.stringify(newData) === JSON.stringify(backupData)
    ) {
      console.log("No changes detected. Data is already up to date.");
      return true;
    }

    // Write newData to data.json
    fs.writeFileSync(dataPath, JSON.stringify(newData, null, 2), "utf8");
    console.log("Data successfully written to data.json!");

    // Replicate newData to data-back.json
    fs.writeFileSync(backupPath, JSON.stringify(newData, null, 2), "utf8");
    console.log("Backup successfully created in data-back.json!");

    return true;
  } catch (err) {
    console.error("Error writing to JSON file:", err);
    return false;
  }
};

class RelayManager {
  constructor(waitingTime = 10) {
    this.waitingTime = waitingTime; // Default waiting time in minutes
    this.groups = {}; // Stores all the groups, each with its racks and relays
  }

  createGroup(groupId) {
    if (!this.groups[groupId]) {
      this.groups[groupId] = {
        globalRelayState: false,
        racks: {},
      };
      console.log(`Group ${groupId} created.`);
    } else {
      console.log(`Group ${groupId} already exists.`);
    }
  }

  createRack(groupId, rackId) {
    const group = this.groups[groupId];
    if (group) {
      if (!group.racks[rackId]) {
        group.racks[rackId] = Array.from({ length: 4 }, () => ({
          time: 0,
          waitState: false,
        }));
        console.log(`Rack ${rackId} created in Group ${groupId}.`);
      } else {
        console.log(`Rack ${rackId} already exists in Group ${groupId}.`);
      }
    } else {
      console.log(`Group ${groupId} does not exist.`);
    }
  }

  removeGroup(groupId) {
    if (this.groups[groupId]) {
      delete this.groups[groupId];
      console.log(`Group ${groupId} and all its racks have been removed.`);
    } else {
      console.log(`Group ${groupId} does not exist.`);
    }
  }

  removeRack(groupId, rackId) {
    const group = this.groups[groupId];
    if (group && group.racks[rackId]) {
      delete group.racks[rackId];
      console.log(`Rack ${rackId} removed from Group ${groupId}.`);
    } else {
      console.log(`Group ${groupId} or Rack ${rackId} does not exist.`);
    }
  }

  changeState(groupId, rackId, relayIndex, state) {
    const group = this.groups[groupId];
    const rack = group?.racks[rackId];
    const relay = rack?.[relayIndex];
    if (relay) {
      if (state === "OFF") {
        relay.time = 0;
        relay.waitState = false;
      } else if (state === "ON") {
        relay.time = this.waitingTime;
        relay.waitState = true;
      }
    } else {
      console.log(
        `Group ${groupId}, Rack ${rackId}, or Relay ${relayIndex} does not exist.`
      );
    }
  }

  checkGroupState() {
    for (const [groupId, groupData] of Object.entries(this.groups)) {
      let isAnyRelayOn = false;

      for (const [rackId, relays] of Object.entries(groupData.racks)) {
        relays.forEach((relay) => {
          if (relay.waitState) {
            if (relay.time === 0) {
              isAnyRelayOn = true;
            } else {
              relay.time -= 1; // Decrement time if still counting down
            }
          }
        });
      }

      groupData.globalRelayState = isAnyRelayOn;
      if (isAnyRelayOn) {
        this.turnOnRelay(groupId);
      } else {
        this.turnOffRelay(groupId);
      }
    }
  }

  async turnOnRelay(groupId) {
    console.log(`Group ${groupId} Relay State: ON`);
    let cache = await get_data();

    let group = cache.find((group) => group.Group_id === groupId);

    group.racks[0]["relay_on"] = true;

    set_data(cache);
  }

  async turnOffRelay(groupId) {
    let cache = await get_data();

    let group = cache.find((group) => group.Group_id === groupId);

    if (group && group.racks.length > 0) {
      group.racks[0]["relay_on"] = false;
      set_data(cache);
    }
  }

  // New method to print all groups and their respective racks
  printGroupsAndRacks() {
    console.log("Available Groups and their respective Racks:");
    for (const [groupId, groupData] of Object.entries(this.groups)) {
      console.log(`Group ${groupId}:`);
      for (const [rackId, relays] of Object.entries(groupData.racks)) {
        console.log(`  Rack ${rackId}:`);
        relays.forEach((relay, index) => {
          console.log(
            `    Relay ${index}: Time ${relay.time} minutes, WaitState: ${relay.waitState}`
          );
        });
      }
    }
  }
}

module.exports = RelayManager;
