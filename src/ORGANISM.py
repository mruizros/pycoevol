###############################################################################
# Encoding utf-8                                                              #
# Created by F. Madeira, 2012                                                 #
# This code is part of Pycoevol distribution.                                 #
# This work is public domain.                                                 #
###############################################################################

from Parameters import pairwise_distance, pairwise_trim
from Parameters import correlation_method
from os import remove, system, chdir
from numpy import mean, sqrt, log, median
from math import e
from collections import OrderedDict
from Bio import SeqIO, AlignIO
from Bio.Alphabet import IUPAC
from Bio.Align.Applications import ClustalwCommandline

    
class organism:
    """
    Main code for sort and selection of organisms. 
    
    Methods for calculate distance between pairwise alignments:
    p-distance - Jukes and Cantor, 1969
    Jukes-Cantor - Jukes and Cantor, 1969
    Kimura Distance - Kimura, 1983
    Alignment score - ??
    """
    def __init__(self, id1, id2, psiblast):
        self.id1 = str(id1)
        self.id2 = str(id2)
        self.psiblast = psiblast
    def __call__(self, id1, id2, psiblast):
        self.id1 = str(id1)
        self.id2 = str(id2)
        self.psiblast = psiblast
        
    def uniqueOrganism(self, id1, id2):
        "Selects best hit for each matching organism"
        
        input1 = "./Data/" + id1 + ".blast"
        ord_dict1 = orderedDict(SeqIO.parse(input1, "fasta",IUPAC.protein), 
                                key_function=checkOrganism)
        
        input2 = "./Data/" + id2 + ".blast"
        ord_dict2 = orderedDict(SeqIO.parse(input2, "fasta",IUPAC.protein), 
                                key_function=checkOrganism)
        
        sequences1 = {}
        seq1 = []
        for keys1 in ord_dict1.keys():
            if keys1 in ord_dict2.keys():
                organism = ord_dict1[keys1].description
                sequence = ord_dict1[keys1].seq
                seq1.append(organism)
                sequences1[organism] = sequence
        
        sequences2 = {}
        seq2 = []
        for keys2 in ord_dict2.keys():
            if keys2 in ord_dict1.keys():
                organism = ord_dict2[keys2].description
                sequence = ord_dict2[keys2].seq
                seq2.append(organism)
                sequences2[organism] = sequence

        if seq1 == [] or seq2 == []:
            raise StandardError, "There is no matching organisms"
        elif len(seq1) < 15 or len(seq2) <15:
            raise StandardError, "Number of matching organisms < 15"
        else: pass
        
        organism = []
        list = []
        for org in seq1:
            if org in seq2:
                value = [seq1.index(org) + seq2.index(org), 
                         seq1.index(org), seq2.index(org), org]
                list.append(value)
        sort = sorted(list)
        for index in sort:
            org = index[3]
            organism.append(org)
        
        self.ord_sequences1 = []
        self.ord_sequences2 = []
        for org in organism:
            value = [org, str(sequences1[org])]
            self.ord_sequences1.append(value)
            value = [org, str(sequences2[org])]
            self.ord_sequences2.append(value)
        
        return self.ord_sequences1, self.ord_sequences2
        
        
    def trimSequence(self, id1, id2, trim=True, method=None):
        """
        Trims the set of sequences by pairwise alignment with the query.
        Calculates distance between each pair by diferent methods:
        p-distance, Jukes-Cantor and Alignment score with BLOSUM62 matrix.
        (pdistance, jukescantor, alignscore - edit Parameters.py)
        """
        
        trim = pairwise_trim
        method = pairwise_distance
        distances1 = []
        distances2 = []
        
        input = "./Data/" + id1 + ".fasta"
        input_query = SeqIO.parse(input, "fasta", IUPAC.protein)
        for record in input_query:
            q_desc = str(record.description)
            q_seq = str(record.seq)
            break
           
        for entry in self.ord_sequences1:
            p_desc = str(entry[0])
            p_seq = str(entry[1])
                       
            pair = "./Data/" + id1 + ".pair"
            out_pair= open(pair, "w")
            
            sequence1 = str("\n" + ">" +q_desc + "\n" + q_seq + "\n")
            sequence2 = str("\n" + ">" + p_desc + "\n" + p_seq + "\n")
            out_pair.write(sequence1 + sequence2)
            out_pair.close()    
            
            output_align = "./Data/" + id1 + "_pair.aln"
            output_tree = "./Data/" + id1 + "_pair.dnd"
            clustalw = ClustalwCommandline(infile=pair, 
                                           outfile=output_align, 
                                           newtree=output_tree, 
                                           align="input", 
                                           quiet="input", 
                                           seqnos="ON", 
                                           outorder="input", 
                                           type="PROTEIN", 
                                           pwmatrix="GONNET", 
                                           gapopen=10, 
                                           gapext=0.2) 
            clustalw()
            
            if trim == True:
                alignment = AlignIO.read(output_align, "clustal")
                length = alignment.get_alignment_length()
                for s in range(0,length,1):
                    column = alignment[:, s]
                    if column[0] != "-":
                        start = s
                        break
                for e in range(int(length-1), 0, -1):
                    column = alignment[:, e]
                    if column[0] != "-":
                        end = e
                        break
            
                p_new_seq = p_seq[int(start):int(end)]            
            
                output = "./Data/" + id1 + ".fasta"
                out_fasta = open(output, "a")
                out_fasta.write("\n" + ">" + p_desc + "\n" + p_new_seq + "\n")
                out_fasta.close()
            else: pass
            
            if method != None:
                output_fasta = "./Data/" + id1 + "_pair.fasta"
                AlignIO.convert(output_align, "clustal", output_fasta, "fasta")
            
                input_align = SeqIO.parse(output_fasta, "fasta", IUPAC.protein)
                msa = []
                for record in input_align:
                    seq = str(record.seq)
                    msa.append(seq)
                sequence1 = msa[0]
                sequence2 = msa[1]
            
                pair_score = getDistance(sequence1, sequence2, method)
                distances1.append(pair_score)
            else: pass
                
        try:
            remove(pair)
            remove(output_align)
            remove(output_tree)
            remove(output_fasta)
        except:
            pass
        
        input = "./Data/" + id2 + ".fasta"
        input_query = SeqIO.parse(input, "fasta", IUPAC.protein)
        for record in input_query:
            q_desc = str(record.description)
            q_seq = str(record.seq)
            break
        
        for entry in self.ord_sequences2:
            p_desc = str(entry[0])
            p_seq = str(entry[1])
                       
            pair = "./Data/" + id2 + ".pair"
            out_pair= open(pair, "w")
            
            sequence1 = str("\n" + ">" + q_desc + "\n" + q_seq + "\n")
            sequence2 = str("\n" + ">" + p_desc + "\n" + p_seq + "\n")
            out_pair.write(sequence1 + sequence2)
            out_pair.close()    
            
            output_align = "./Data/" + id2 + "_pair.aln"
            output_tree = "./Data/" + id2 + "_pair.dnd"
            clustalw = ClustalwCommandline(infile=pair, 
                                           outfile=output_align, 
                                           newtree=output_tree, 
                                           align="input", 
                                           quiet="input", 
                                           seqnos="ON", 
                                           outorder="input", 
                                           type="PROTEIN", 
                                           pwmatrix="GONNET", 
                                           gapopen=10, 
                                           gapext=0.2) 
            clustalw()
            
            if trim == True:
                alignment = AlignIO.read(output_align, "clustal")
                length = alignment.get_alignment_length()
                for s in range(0,length,1):
                    column = alignment[:, s]
                    if column[0] != "-":
                        start = s
                        break
                for e in range(int(length-1), 0, -1):
                    column = alignment[:, e]
                    if column[0] != "-":
                        end = e
                        break
            
                p_new_seq = p_seq[int(start):int(end)]            
            
                output = "./Data/" + id2 + ".fasta"
                out_fasta = open(output, "a")
                out_fasta.write("\n" + ">" + p_desc + "\n" + p_new_seq + "\n")
                out_fasta.close()
            else: pass
            
            if method != None:
                output_fasta = "./Data/" + id2 + "_pair.fasta"
                AlignIO.convert(output_align, "clustal", output_fasta, "fasta")
            
                input_align = SeqIO.parse(output_fasta, "fasta", IUPAC.protein)
                msa = []
                for record in input_align:
                    seq = str(record.seq)
                    msa.append(seq)
                sequence1 = msa[0]
                sequence2 = msa[1]
            
                pair_score = getDistance(sequence1, sequence2, method)
                distances2.append(pair_score)
            else: pass
                
        try:
            remove(pair)
            remove(output_align)
            remove(output_tree)
            remove(output_fasta)
        except:
            pass
        
        if method != None:
            output = "./Data/matrix.txt" 
            out_distance = open(output, "w")
            for i in range(len(distances1)):
                print >> out_distance, "1" + "\t" + str(i+2) + "\t" + \
                                            str(distances1[i]) + "\t" + \
                                            str(distances2[i])
            out_distance.close()
        else: pass
    
    def getsCorrelation(self, method=None):
        """
        Uses phylogen -t using method='phylogen'or a 
        python implementation of the Theil-Sen Estimator.
        Calculates the correlation, a distance between 
        each point P(x,y) to the mean slope. Distance of
        P(m,n) to Ax+By+C=0 is d=Abs(Am+Bn+C)/Sqrt(A^2+B^2)
        """
        try:
            input =str("./Data/matrix.txt")
            file = open(input,"r")
            file.close() 
        except:    
            return
        
        method = correlation_method
        if method == "phylogen":
            chdir("./Data/")
            phylogen = system("phylogen.exe -t matrix.txt > correlation.txt") 
            phylogen    
            chdir("../")
        else:
            input = "./Data/matrix.txt"
            input_matrix = open(input, "r")
            matrix = input_matrix.readlines()
            input_matrix.close()
            
            Xs = []
            Ys = []
            for line in matrix:
                l = line.rstrip("\n")
                l = l.split()
                X = float(l[2])
                Y = float(l[3])
                Xs.append(X)
                Ys.append(Y)
            slope = theilsenEstimator(Xs,Ys)
            
            m = abs(slope)
            divisor = sqrt(1 + sqrt(m))
            distance = []
            for f in range(len(Xs)):
                d = abs(m*Xs[f] + Ys[f])/divisor
                distance.append(d)
            
            output = "./Data/correlation.txt"
            out_correlation = open(output, "w")
            print >> out_correlation, "Slope: %s" %(str(slope))
            for d in range(len(distance)):
                print >> out_correlation, str(d+2) + "\t" + str(distance[d])
            out_correlation.close()
                 

    def removeSequences(self, id1, id2):
        """
        Removes sequences that not correlate and are point out by the
        Theil-Sen estimator. It implements an easy algorithm to remove 
        distante sequences.
        """
        try:
            input =str("./Data/correlation.txt")
            file = open(input,"r")
            file.close() 
        except:    
            return
        
        input = "./Data/correlation.txt"
        input_correlation= open(input, "r")
        correlation = input_correlation.readlines()
        input_correlation.close()
        
        value = []
        for line in correlation:
            if ":" in line:
                pass
            else:
                l = line.rstrip("\n")
                l = l.split("\t")
                seq = int(l[0])
                d = float(l[1])
                if seq != 0:
                    value.append(d)    
        
        removed = []
        threshold = 0.5 # cut less ->1; cut more ->0
        maximum = max(value)
        minimum = min(value)
        median_all = median(value)
        median_min = median_all - ((median_all - minimum) * 1.0 * threshold)
        median_max = median_all + ((maximum - median_all) * 1.0 * threshold)
        for v in value:
            if v < median_min or v > median_max:
                position = value.index(v)    
                removed.append(position+1)
            else: pass       
        
        if removed != 0:
            sequences1 = []
            input = "./Data/" + id1 + ".fasta"
            input_sequences = SeqIO.parse(input, "fasta", IUPAC.protein)
            for record in input_sequences:
                desc = record.description
                seq = record.seq
                value = [str(desc),str(seq)]
                sequences1.append(value)
               
            output_fasta = open(input, "w") 
            for i in range(len(sequences1)):
                if i not in removed:
                    desc = str(sequences1[i][0])
                    seq =  str(sequences1[i][1])
                    output_fasta.write(">" + desc + "\n" + seq + "\n" + "\n")
                else: 
                    pass
            output_fasta.close()
            
            
            sequences2 = []
            input = "./Data/" + id2 + ".fasta"
            input_sequences = SeqIO.parse(input, "fasta", IUPAC.protein)
            for record in input_sequences:
                desc = record.description
                seq = record.seq
                value = [str(desc),str(seq)]
                sequences2.append(value)
            
            output_fasta = open(input, "w")    
            for i in range(len(sequences2)):
                if i not in removed:
                    desc = str(sequences2[i][0])
                    seq =  str(sequences2[i][1])
                    output_fasta.write(">" + desc + "\n" + seq + "\n" + "\n")
                else: 
                    pass
            output_fasta.close()
        else: pass
            
 
def theilsenEstimator(Xs,Ys):
    """
    The Theil-Sen estimator calculates the median slope 
    among all lines through pairs of two-dimensional 
    sample points.
    """
    assert len(Xs) == len(Ys)
    slopes = []
    for f in range(0,len(Xs)-1):
        x1 = Xs[f]
        y1 = Ys[f]
        for g in range(1,len(Ys)):
            x2 = Xs[g]
            y2 = Ys[g]
            if x1 != x2:
                slope = (y2 - y1) / (x2 - x1)
                slopes.append(slope)
    
    slope = mean(slopes)
    return slope
        
def matchScore(alpha, beta, matrix):
    "Matches scores from a matrix"
    
    alphabet = {}    
    alphabet["A"] = 0
    alphabet["R"] = 1
    alphabet["N"] = 2
    alphabet["D"] = 3
    alphabet["C"] = 4
    alphabet["Q"] = 5
    alphabet["E"] = 6
    alphabet["G"] = 7
    alphabet["H"] = 8
    alphabet["I"] = 9
    alphabet["L"] = 10
    alphabet["K"] = 11
    alphabet["M"] = 12
    alphabet["F"] = 13
    alphabet["P"] = 14
    alphabet["S"] = 15
    alphabet["T"] = 16
    alphabet["W"] = 17
    alphabet["Y"] = 18
    alphabet["V"] = 19
    alphabet["B"] = 20
    alphabet["Z"] = 21
    alphabet["X"] = 22
    alphabet["-"] = 22
    lut_x = alphabet[alpha]
    lut_y = alphabet[beta]
    
    return mapMatrix(matrix)[lut_x][lut_y]
    
def mapMatrix(matrix):
    "Maps a matrix of floats"
    matrix = matrix.upper()
    
    score_matrix = []
    input = './Matrix/' + matrix
    input_matrix = open(input, 'r')
    for line in input_matrix.readlines():
        score_matrix.append(map(float, line.split()))
    input_matrix.close()
    
    return score_matrix
    
def checkOrganism(record):
    "Defines organism keys for a dictionary"
    organism = record.description.rstrip("\n")
    return organism
    
def orderedDict(sequences, key_function=None):
    "Defines an ordered dictionary"
    d = OrderedDict()               
    for record in sequences:
        key = key_function(record)
        if key in d:
            pass
        d[key] = record
    return d

def ln(n): 
    return log(n) * 1.0 / log(e)
     
def getDistance(sequence1, sequence2, method):
    "Returns the distance between the sequences"       
    if method == "pdistance":
        distance = pDistance(sequence1,sequence2) 
    elif method == "jukescantor":
        distance = jukesCantor(sequence1,sequence2)
    elif method == "kimura":
        distance = kimuraDistance(sequence1,sequence2)
    elif method == "alignscore":
        distance = alignmentScore(sequence1,sequence2)
    else: 
        raise StandardError, "%s - Invalid method for distance calculation" %(method)  
    return distance

def pDistance(sequence1,sequence2):
    """
    Proportion of sites at which the two sequences are different. 
    p is close to 1 for poorly related sequences, and p is close 
    to 0 for similar sequences. d = p
    """
    assert len(sequence1) == len(sequence2)
    
    match = 0
    for a,b in zip(sequence1, sequence2):
        if a!=b:
            match += 1
        else:
            pass
    
    length = len(sequence1)
    score = match * 1.0 / length
    score = score
    return score


def jukesCantor(sequence1,sequence2):
    """
    Maximum likelihood estimate of the number of substitutions 
    between two sequences. p is described with the method 
    p-distance. d = -19/20 log(1 - p * 20/19)
    """
    exterior = -19 * 1.0 / 20
    interior = 1 - pDistance(sequence1,sequence2) * 20 * 1.0 / 19
    score = exterior * log(interior)
    
    score = str(score)
    if score == "nan":
        score = str(0.0)
    else: pass
    
    return score

def kimuraDistance(sequence1,sequence2):
    """
    Kimura's distance. This is a rough-and-ready distance formula 
    for approximating PAM distance by simply measuring the fraction 
    of amino acids, p, that differs between two sequences and 
    computing the distance as (Kimura, 1983).
    d = - log_e (1 - p - 0.2 p^2 ). 
    """
    
    p_distance = pDistance(sequence1,sequence2)
    interior = (1 - p_distance - 0.2 * p_distance**2)
    score = -ln(interior)
    
    score = str(score)
    if score == "nan":
        score = str(0.0)
    else: pass
    
    return score

def alignmentScore(sequence1,sequence2):
    """
    Distance (d) between two sequences (1, 2) is computed from 
    the pairwise alignment score between the two sequences (score12), 
    and the pairwise alignment score between each sequence and itself 
    (score11, score22). This metric ignores gaps.
    d = (1-score12/score11)* (1-score12/score22)
    
    !!Disclaimer: alignmentScore is terribly slow!!
    """
    assert len(sequence1) == len(sequence2)
    
    score12 = 0     
    for i in sequence1:
        for j in sequence2:
            if i != "-" or j != "-":
                score12 += float(matchScore(i, j, "BLOSUM62"))
            else: pass
            
    score11 = 0     
    for i in sequence1:
        for j in sequence1:
            if i != "-" or j != "-":
                score11 += float(matchScore(i, j, "BLOSUM62"))
            else: pass
    
    score22 = 0     
    for i in sequence2:
        for j in sequence2:
            if i != "-" or j != "-":
                score22 += float(matchScore(i, j, "BLOSUM62"))
            else: pass
    
    part1 = (1 - score12 * 1.0 / score11)
    part2 = (1 - score12 * 1.0 / score22)
    
    score = part1 * part2
    return score
