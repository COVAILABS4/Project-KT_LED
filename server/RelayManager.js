// RelayManager.js

const { group } = require("console");
const fs = require("fs");

const get_data = () => {
  try {
    const jsonData = fs.readFileSync("./data.json", "utf8");
    return JSON.parse(jsonData);
  } catch (err) {
    console.error("Error reading JSON file:", err);
    return null;
  }
};

// Method to set data in data.json
const set_data = (newData) => {
  try {
    fs.writeFileSync("./data.json", JSON.stringify(newData, null, 2), "utf8");
    console.log("Data successfully updated!");
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

  turnOnRelay(groupId) {
    console.log(`Group ${groupId} Relay State: ON`);
    let cache = get_data();

    let group = cache.find((group) => group.Group_id === groupId);

    group.racks[0]["relay_on"] = true;

    set_data(cache);
  }

  turnOffRelay(groupId) {
    let cache = get_data();

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
