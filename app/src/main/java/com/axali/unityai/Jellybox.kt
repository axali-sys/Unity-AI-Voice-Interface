package com.axali.unityai

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import android.content.ContentValues

class Jellybox(context: Context) : SQLiteOpenHelper(context, "jellybox.db", null, 1) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("CREATE TABLE memories (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, created_at INTEGER NOT NULL)")
    }
    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {}
    fun save(content: String) {
        writableDatabase.insert("memories", null, ContentValues().apply {
            put("content", content)
            put("created_at", System.currentTimeMillis())
        })
    }
    fun count(): Int = readableDatabase.rawQuery("SELECT COUNT(*) FROM memories", null).use {
        if (it.moveToFirst()) it.getInt(0) else 0
    }
}
