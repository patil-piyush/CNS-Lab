#include <iostream>
#include <vector>

using namespace std;



int main() {
    
    // Taking inputs from user
    int dwLength=0, dLength =0;
    cout<<"Enter the number of bits in Dataword: ";
    cin>>dwLength;
    int dataword[dwLength];
    cout<<"Enter the Dataword bits: ";
    for(int i = 0; i<dwLength; i++){
        cin>>dataword[i];
    }
    
    cout<<"Enter the number of bits in Divisor: ";
    cin>>dLength;
    int divisor[dLength];
    cout<<"Enter the Divisor bits: ";
    for(int i = 0; i<dLength; i++){
        cin>>divisor[i];
    }
    
    // creating divident
    int divident[dwLength + dLength - 1];
    for(int i = 0; i<dwLength + dLength - 1; i++){
        if(i<dwLength){
            divident[i] = dataword[i];
        }
        else{
            divident[i] =0;
        }
    }
    
    // declaration of other data storages
    vector<int> rem;
    vector<int> quotient;
    int curr=4;
    
    for(int i = 0; i<dwLength; i++){
        rem.push_back(divident[i]);
    }
    
    while((rem.size() >= 4) && (curr<= dwLength + dLength - 1)){
        if(rem[0]<divisor[0]){
            for(int i=1;i<rem.size();i++){
                rem[i-1] = rem[i]^0;
            }
            rem[3] = divident[curr++];
            quotient.push_back(0);
        }
        else{
            for(int i=1;i<rem.size();i++){
                rem[i-1] = rem[i]^divisor[i];
            }
            rem[3] = divident[curr++];
            quotient.push_back(1);
        }
    }
    rem.pop_back();
    
    for(int q:quotient){
        cout<<q<<" ";
    }
    cout<<endl;
    for(int q:rem){
        cout<<q<<" ";
    }
    
    
    return 0;
}
