// Prints the lines DocC highlights for each (previousFile, file) pair.
//
// DocC highlights a code step by taking the insertions of
// `newLines.difference(from: oldLines)`, so the only reliable way to know which
// lines light up is to run the same standard-library diff. generate_snapshots.py
// pipes a JSON array of {"old": ..., "new": ...} objects to this script and reads
// back a JSON array with one list of 1-based line numbers per pair.

import Foundation

struct Pair: Decodable {
    let old: String
    let new: String
}

func lines(_ text: String) -> [String] {
    text.split(omittingEmptySubsequences: false, whereSeparator: { $0.isNewline }).map(String.init)
}

let input = FileHandle.standardInput.readDataToEndOfFile()
let pairs = try JSONDecoder().decode([Pair].self, from: input)
let highlights: [[Int]] = pairs.map { pair in
    lines(pair.new).difference(from: lines(pair.old)).insertions.compactMap { change in
        guard case .insert(let offset, _, _) = change else { return nil }
        return offset + 1
    }
}
FileHandle.standardOutput.write(try JSONEncoder().encode(highlights))
