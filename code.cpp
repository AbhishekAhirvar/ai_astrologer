#include <iostream>
#include<vector>
#include<algorithm>
#include<unordered_map>
using namespace std;

int mirrorDistance(int n) {
        long long rev =0;
        long long original =n;
        while(n>0){
        int x= n%10;
        int rev = rev*10+x;
        n=n/10;
        }
        return abs(original-rev);
    }

    long long mincost(string s,vector <int> &cost){
        //calculate cost of each character
        unordered_map<char,int> mp;
        
    }

    //

int main() {
int x = mirrorDistance(19);
cout<<x;
return 0;}