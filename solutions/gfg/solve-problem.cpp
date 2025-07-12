#include <bits/stdc++.h>
using namespace std;

class Solution{
public:
    int maxGold(int n, int m, vector<vector<int>> M)
    {
        int dp[n][m];
        for(int j=m-1; j>=0; j--){
            for(int i=0; i<n; i++){
                if(j==m-1)
                    dp[i][j] = M[i][j];
                else{
                    int right = M[i][j];
                    if(i-1>=0) right = max(right, M[i][j]+dp[i-1][j+1]);
                    if(i+1<n) right = max(right, M[i][j]+dp[i+1][j+1]);
                    right = max(right, M[i][j] + dp[i][j+1]);
                    dp[i][j] = right;
                }
            }
        }
        int ans = INT_MIN;
        for(int i=0; i<n; i++){
            ans = max(ans, dp[i][0]);
        }
        return ans;
    }
};