#include <iostream>
#include <vector>
using namespace std;

// Function to perform CRC division
vector<int> crcDivision(vector<int> dividend, vector<int> divisor) {
    int n = divisor.size();
    int m = dividend.size();

    vector<int> rem(dividend.begin(), dividend.begin() + n);

    int curr = n;
    while (curr < m) {
        if (rem[0] == 1) {
            for (int i = 1; i < n; i++) {
                rem[i - 1] = rem[i] ^ divisor[i];
            }
        } else {
            for (int i = 1; i < n; i++) {
                rem[i - 1] = rem[i];  // just shift
            }
        }
        rem[n - 1] = dividend[curr++];
    }

    // final step: one last division if leading bit = 1
    if (rem[0] == 1) {
        for (int i = 1; i < n; i++) {
            rem[i - 1] = rem[i] ^ divisor[i];
        }
        rem[n - 1] = 0;
    } else {
        for (int i = 1; i < n; i++) {
            rem[i - 1] = rem[i];
        }
        rem[n - 1] = 0;
    }

    rem.erase(rem.begin()); // remove the leading bit
    return rem; // size = n-1
}


int main() {
    int dwLength, dLength;
    cout << "Enter the number of bits in Dataword (7 or 8 for ASCII): ";
    cin >> dwLength;

    vector<int> dataword(dwLength);
    cout << "Enter the Dataword bits: ";
    for (int i = 0; i < dwLength; i++) cin >> dataword[i];

    cout << "Enter the number of bits in Divisor: ";
    cin >> dLength;

    vector<int> divisor(dLength);
    cout << "Enter the Divisor bits: ";
    for (int i = 0; i < dLength; i++) cin >> divisor[i];

    // Step 1: Create dividend = dataword + (dLength-1) zeros
    vector<int> dividend = dataword;
    for (int i = 0; i < dLength - 1; i++) dividend.push_back(0);

    // Step 2: Perform division to get remainder
    vector<int> remainder = crcDivision(dividend, divisor);

    // Step 3: Append remainder to original dataword → codeword
    vector<int> codeword = dataword;
    for (int bit : remainder) {
        codeword.push_back(bit);
    }

    // Output
    cout << "Remainder (CRC bits): ";
    for (int bit : remainder) cout << bit;
    cout << endl;

    cout << "Codeword to be transmitted: ";
    for (int bit : codeword) cout << bit;
    cout << endl;

    return 0;
}
