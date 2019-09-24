<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    version="1.0" xmlns:ead="urn:isbn:1-931666-22-9">
    <xsl:output method="text"/>
    <xsl:variable name="varTab">
        <xsl:text>&#x9;</xsl:text>
    </xsl:variable>
    <!-- Set language code at the start of a project. Should be 3-letter NISO encoding, typically 'eng' or 'zxx' -->
    <xsl:variable name="langCode">
        <xsl:text>Language</xsl:text>
    </xsl:variable>
    <!-- Set Digital Commonwealth genre type here. Must be one of the 20 headings listed in the DC-BPL MODS guidelines. Word only, Aspace handles the authority code. -->
    <xsl:variable name="DCGenre">
        <xsl:text>Genre</xsl:text>
    </xsl:variable>
    <!-- Set Digital Commonwealth typeOfResource here. Must be one of the 11 options listed in the DC-BPL MODS guidelines. -->
    <xsl:variable name="typeOfResource">
        <xsl:text>typeOfResource</xsl:text>
    </xsl:variable>
    <xsl:template match="/">
        <xsl:for-each select="//ead:did/ead:unitid">
            <xsl:if test="ancestor::ead:c[@level='file'] or ancestor::ead:c[@level='item']" >
                <xsl:call-template name="DAO"/>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template name="DAO">
        <xsl:value-of select="."/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="ancestor::ead:c[1]/@id"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="ancestor::ead:c[1]/@level"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of
            select="normalize-space(//ead:ead/ead:archdesc[@level='collection']/ead:userestrict/ead:p)"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="ead:unitdate/@normal"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="$langCode"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="$DCGenre"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="$typeOfResource"/>
        <xsl:text>
</xsl:text>
    </xsl:template>
</xsl:stylesheet>