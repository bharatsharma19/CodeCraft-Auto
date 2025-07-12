#include <vector>
#include <algorithm>
#include <string>
#include <unordered_map>
#include <queue>
#include <stack>
#include <set>
#include <map>
#include <iostream>
#include <functional>
#include <utility>
#include <climits>
#include <tuple>

using namespace std;

class Solution {
private:
    map<tuple<int, int, int>, pair<int, int>> memo;

    pair<int, int> solve(int k, int p1, int p2) {
        if (p1 > p2) {
            swap(p1, p2);
        }
        
        // Canonical state representation
        if (p1 + p2 > k + 1) {
            p1 = k + 1 - p2;
            p2 = k + 1 - p1;
        }
        
        // Base case: players meet in this round
        if (p1 + p2 == k + 1) {
            return make_pair(1, 1);
        }

        tuple<int, int, int> state = make_tuple(k, p1, p2);
        if (memo.count(state)) {
            return memo.at(state);
        }

        int k_next = (k + 1) / 2;
        int l = p1 - 1;
        int m = p2 - p1 - 1;
        int r_count = k - p2;

        int winners_to_pick = k_next - 2;
        
        int min_res = INT_MAX;
        int max_res = INT_MIN;
        
        // Determine range of possible winners from the left group
        int w_l_min = max(0, winners_to_pick - m - r_count);
        int w_l_max = min(l, winners_to_pick);

        // Iterate through all possible outcomes for other matches
        for (int w_l = w_l_min; w_l <= w_l_max; ++w_l) {
            int p1_next = 1 + w_l;
            int rem_winners = winners_to_pick - w_l;
            
            // Determine range of possible winners from the middle group
            int w_m_min = max(0, rem_winners - r_count);
            int w_m_max = min(m, rem_winners);
            
            for (int w_m = w_m_min; w_m <= w_m_max; ++w_m) {
                int p2_next = p1_next + 1 + w_m;
                pair<int, int> sub_res = solve(k_next, p1_next, p2_next);
                min_res = min(min_res, sub_res.first);
                max_res = max(max_res, sub_res.second);
            }
        }
        
        pair<int, int> result = make_pair(1 + min_res, 1 + max_res);
        memo[state] = result;
        return result;
    }

public:
    vector<int> earliestAndLatest(int n, int firstPlayer, int secondPlayer) {
        pair<int, int> res = solve(n, firstPlayer, secondPlayer);
        vector<int> final_result;
        final_result.push_back(res.first);
        final_result.push_back(res.second);
        return final_result;
    }
};