import os.path
import csv


ERROR_MRG = -1
ERROR_DB_FILE_NOT_FOUND = -2
ERROR_DB_TOKEN_NOT_FOUND = -3
ERROR_DB_EDS_NODE_NOT_FOUND = -4
ERROR_DB_SEMLINK_NOT_MATCHED = -5

TASK1_HEADER = ['filePath', 'lineNumber', 'text', 'classification']
TASK2_HEADER = ['filePath', 'lineNumber', 'text']
TASK1 = []
TASK2 = []

def get_actual_word_index(fileName, sentenceIndex, wordIndex):
    wordList = []
    addSymbol = ''
    prevWord = ''
    
    with open(fileName, 'r') as PTBreader:
        line = PTBreader.readline()

        while sentenceIndex:
            if len(line.strip()) == 0:
                    sentenceIndex -= 1

            line = PTBreader.readline()

        for i in range(wordIndex):
            lineList = line.split()
            currWord = lineList[-1].strip(')')
            if lineList[-2][-6:] == '-NONE-':
                line = PTBreader.readline()
                continue
            elif lineList[-1].strip(')') == '.':
                line = PTBreader.readline()
                continue
            elif lineList[-1] == '-)':
                prevWord = wordList.pop()
                addSymbol = '-'
                line = PTBreader.readline()
                continue
            elif lineList[-1] == '/)':
                prevWord = wordList.pop()
                addSymbol = '/'
                line = PTBreader.readline()
                continue


            if addSymbol:
                newWord = prevWord + addSymbol + currWord
                wordList.append(newWord)
                addSymbol = ''
                prevWord = ''
            else:
                wordList.append(currWord)

            line = PTBreader.readline()

    return len(wordList)


def find_deepbank_EDS_node(filePath, nodeIndex, word):

    lineNum = 1

    hyphen = word.find('-')
    word = word[:hyphen]

    with open(filePath, 'r') as DBreader:
        line = DBreader.readline()

        while line and line.strip() != '<':
            line = DBreader.readline()
            lineNum += 1

        line = DBreader.readline()
        lineNum += 1

        for i in range(nodeIndex):
            line = DBreader.readline()
            lineNum += 1
            if not line or line.strip() == '>':
                print("Error: DeepBank token not found in file", filePath)
                return ERROR_DB_TOKEN_NOT_FOUND, ''


        nodeLine = line
        lineList = line.split()
        position = lineList[3]
        identifier = position[:-1]


        nextLine = DBreader.readline()
        lineNum += 1
        if nextLine.strip() == '>':
            print("Error: DeepBank reached last token in file", filePath)
            return ERROR_DB_TOKEN_NOT_FOUND, ''

        nextLineList = nextLine.split()

        if nextLineList[5][:-1] == '"."' or nextLineList[5][:-1] == '","':
            colon = identifier.find(':')
            num = identifier[colon+1:-1]
            newNum = int(num) + 1
            newIdentifier = identifier[:colon+1] + str(newNum) + '>'
            identifier = newIdentifier

        while line and line[0] != '{':
            line = DBreader.readline()
            lineNum += 1

        while line and line.find(identifier) == -1 and line.strip() != '}':
            line = DBreader.readline()
            lineNum += 1


        if not line or line.strip() == '}' or line.strip()[0] != 'e':
            print("Error: DeepBank EDS node not found in file", filePath)
            return ERROR_DB_EDS_NODE_NOT_FOUND, ''

        firstColon = line.find(':')
        lessThan = line.find('<')
        DBword = line[firstColon+2:lessThan]
        for i in range(len(DBword)):
            if not DBword[i].isalpha():
                DBword = DBword[:i]
                break


        if DBword != word:
            print("Error: SemLink and DeepBank predicate not matched in file", filePath)
            return ERROR_DB_SEMLINK_NOT_MATCHED, ''

    return lineNum, line


def insert_framenet(filePath, lineNum, nodeLine, semlinkLine):

    PREFIX = '-fn.'
    predicateNotation = ''

    semlinkList = semlinkLine.split()
    predicateNotation = semlinkList[6]

    if predicateNotation == 'IN' or predicateNotation == 'NF':
        TASK2.append([filePath, lineNum, semlinkLine])
        return False
    else:
        TASK1.append([filePath, lineNum, semlinkLine, predicateNotation])

    lessThan = nodeLine.find('<')
    leftBracket = nodeLine.find('[')

    edges = nodeLine[leftBracket:]
    edgesList = edges.split()

    for s in semlinkList:
        ind = s.find('ARG')
        notation = ''
        if ind != -1 and s[ind+3].isnumeric():
            equal = s.find('=')
            semiColon = s.find(';')
            if semiColon != -1:
                notation = s[semiColon+1:]
            elif equal != -1:
                notation = s[equal+1:]
            
            query = 'ARG' + str(int(s[ind+3]) + 1)

            for i in range(len(edgesList)):
                if edgesList[i].find(query)!= -1 and notation:
                    edgesList[i] = edgesList[i] + PREFIX + notation

    newNodeLine = nodeLine[:lessThan] + PREFIX + predicateNotation + nodeLine[lessThan:leftBracket] + ' '.join(edgesList)

    with open(filePath, 'r') as DBreader:
        lines = DBreader.readlines()
    
    if (lineNum <= len(lines)):
        lines[lineNum - 1] = newNodeLine + '\n'

        with open(filePath, 'w') as DBwriter:
            for line in lines:
                DBwriter.write(line)
    return True


def main():
    lastFile = ''
    lastIndex = -1

    errorMrgCount = 0
    errorDBFileNotFoundCount = 0
    errorDBTokenNotFoundCount = 0
    errorDBEDSNodeNotFoundCount = 0
    errorDBSemlinkNotMatchedCount = 0
    errorFrameNetNotAvailable = 0
    successCount = 0


    with open('1.2.2c.okay', 'r') as SLreader:
        for line in SLreader:
            semlink = line.split()

            if lastFile and semlink[0] == lastFile and lastIndex != -1 and int(semlink[1]) == lastIndex:
                continue
            lastFile = semlink[0]
            lastIndex = int(semlink[1])

            if semlink[0][-4:] == '.mrg':
                errorMrgCount += 1
            else:
                seriesNum = semlink[0][-10:-6]
                sentenceNum = int(semlink[1]) + 1
                sentenceStr = ''
                if sentenceNum > 9:
                    sentenceStr = '0' + str(sentenceNum)
                else:
                    sentenceStr = '00' + str(sentenceNum)
                DBFileName = '2' + str(seriesNum) + sentenceStr
                DBFilePath = 'DeepBank1.1/' + DBFileName

                DBWordIndex = get_actual_word_index(semlink[0], int(semlink[1]), int(semlink[2]))

                if not os.path.isfile(DBFilePath):
                    errorDBFileNotFoundCount += 1
                else:
                    lineNum, nodeLine = find_deepbank_EDS_node(DBFilePath, DBWordIndex, semlink[4])

                    if lineNum == ERROR_DB_TOKEN_NOT_FOUND:
                        errorDBTokenNotFoundCount += 1
                    elif lineNum == ERROR_DB_EDS_NODE_NOT_FOUND:
                        errorDBEDSNodeNotFoundCount += 1
                    elif lineNum == ERROR_DB_SEMLINK_NOT_MATCHED:
                        errorDBSemlinkNotMatchedCount += 1
                    else:
                        if (insert_framenet(DBFilePath, lineNum, nodeLine, line)):
                            successCount += 1
                        else:
                            errorFrameNetNotAvailable += 1

    with open('train.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(TASK1_HEADER)
        writer.writerows(TASK1)

    with open('predict.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(TASK2_HEADER)
        writer.writerows(TASK2)

    print('-----------------------', 'Summary', '-----------------------')
    print('Mrg Error:', errorMrgCount)
    print('DeepBank file not found:', errorDBFileNotFoundCount)
    print('DeepBank token not found:', errorDBTokenNotFoundCount)
    print('DeepBank EDS node not found:', errorDBEDSNodeNotFoundCount)
    print('SemLink and DeepBank predicate not matched:', errorDBSemlinkNotMatchedCount)
    print('FrameNet IN/NF:', errorFrameNetNotAvailable)
    print('Success:', successCount)


if __name__ == "__main__":
    main()