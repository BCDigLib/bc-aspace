<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" exclude-result-prefixes="xs"
    xmlns:fits="http://hul.harvard.edu/ois/xml/ns/fits/fits_output" version="2.0">

    <xsl:output method="text"/>
    <xsl:template match="fits:combined-fits">
    <xsl:text>{</xsl:text>
    <xsl:for-each select="fits:fits">
        <xsl:text>"</xsl:text><xsl:value-of select="fits:fileinfo/fits:filename"/><xsl:text>":</xsl:text>
        <xsl:choose>
            <xsl:when test="fits:identification/fits:identity/@format = 'Waveform Audio'">
                <xsl:call-template name="WaveformAudio"/>
            </xsl:when>   
            <xsl:when test="fits:identification/fits:identity/@format = 'WAVE RF64'">
                <xsl:call-template name="WaveformAudio"/>
            </xsl:when>
            <xsl:when test="fits:identification/fits:identity/@format = 'Portable Document Format'">
                <xsl:call-template name="PDF"/>
            </xsl:when>
            <xsl:when test="fits:identification/fits:identity/@format = 'TIFF EXIF'">
                <xsl:call-template name="TIFF"/>
            </xsl:when>
            <xsl:when test="fits:identification/fits:identity/@format = 'Office Open XML Document'">
                <xsl:call-template name="DOC"/>
            </xsl:when>
            <xsl:when test="fits:identification/fits:identity/@format = 'Microsoft Word Binary File Format'">
                <xsl:call-template name="DOC"/>
            </xsl:when>
            <xsl:when test="fits:identification/fits:identity/@format = 'Quicktime'">
                <xsl:call-template name="MOV"/>
            </xsl:when>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="position() = last()">
                <xsl:text/>
            </xsl:when>
            <xsl:otherwise><xsl:text>,</xsl:text></xsl:otherwise>
        </xsl:choose>
    </xsl:for-each>
        <xsl:text>}</xsl:text>
    </xsl:template>
    
    <!-- Template for WAV audio files -->
    <xsl:template name="WaveformAudio">
        <xsl:text>[{"format":"</xsl:text><xsl:value-of select="fits:identification/fits:identity[1]/@format"/><xsl:text>",</xsl:text>
        <xsl:text>"filesize":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:size"/><xsl:text>",</xsl:text>
        <xsl:text>"checksum":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:md5checksum"/><xsl:text>",</xsl:text>
        <xsl:text>"duration-H:M:S":"</xsl:text><xsl:value-of select="fits:metadata/fits:audio/fits:duration"/><xsl:text>",</xsl:text>
        <xsl:text>"sampleRate":"</xsl:text><xsl:value-of select="fits:metadata/fits:audio/fits:sampleRate"/><xsl:text>",</xsl:text>
        <xsl:text>"bitDepth":"</xsl:text><xsl:value-of select="fits:metadata/fits:audio/fits:bitDepth"/><xsl:text>"}]</xsl:text>
    </xsl:template>    
    
    <!-- Template for PDF files -->
    <xsl:template name="PDF">
        <xsl:text>[{"format":"</xsl:text><xsl:value-of select="fits:identification/fits:identity[1]/@format"/><xsl:text>",</xsl:text>
        <xsl:text>"filesize":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:size"/><xsl:text>",</xsl:text>
        <xsl:text>"checksum":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:md5checksum"/><xsl:text>"}]</xsl:text>
    </xsl:template>
    
    <!-- Template for TIFF files-->
    <xsl:template name="TIFF">
        <xsl:text>[{"format":"</xsl:text><xsl:value-of select="fits:identification/fits:identity[1]/@format"/><xsl:text>",</xsl:text>
        <xsl:text>"filesize":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:size"/><xsl:text>",</xsl:text>
        <xsl:text>"checksum":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:md5checksum"/><xsl:text>",</xsl:text>
        <xsl:text>"pixelDimensions":"</xsl:text><xsl:value-of select="fits:metadata/fits:image/fits:imageWidth"/><xsl:text>x</xsl:text><xsl:value-of select="fits:metadata/fits:image/fits:imageHeight"/><xsl:text>",</xsl:text>
        <xsl:text>"resolution":"</xsl:text><xsl:value-of select="fits:metadata/fits:image/fits:xSamplingFrequency"/><xsl:text>",</xsl:text>
        <xsl:text>"bitsPerSample":"</xsl:text><xsl:value-of select="fits:metadata/fits:image/fits:bitsPerSample/@toolname='Exiftool'"/><xsl:text>",</xsl:text>
        <xsl:text>"colorSpace":"</xsl:text><xsl:value-of select="fits:metadata/fits:image/fits:colorSpace"/><xsl:text>"}]</xsl:text>
    </xsl:template>
    
    <!-- Template for doc and docx files -->
    <xsl:template name="DOC">
        <xsl:text>[{"format":"</xsl:text><xsl:value-of select="fits:identification/fits:identity[1]/@format"/><xsl:text>",</xsl:text>
        <xsl:text>"filesize":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:size"/><xsl:text>",</xsl:text>
        <xsl:text>"checksum":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:md5checksum"/><xsl:text>",</xsl:text>
        <xsl:text>"createDeate":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:created"/><xsl:text>",</xsl:text>
        <xsl:text>"creatingApplicationName":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:creatingApplicationName"/><xsl:text>",</xsl:text>
        <xsl:text>"creatingApplicationVersion":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:creatingApplicationVersion"/><xsl:text>",</xsl:text>
        <xsl:text>"author":"</xsl:text><xsl:value-of select="fits:metadata/fits:document/fits:author"/><xsl:text>",</xsl:text>
        <xsl:text>"title":"</xsl:text><xsl:value-of select="fits:metadata/fits:document/fits:title"/><xsl:text>"}]</xsl:text>
    </xsl:template>
    
    <!-- Template for mov files -->
    <xsl:template name="MOV">
        <xsl:text>[{"format":"</xsl:text><xsl:value-of select="fits:identification/fits:identity[1]/@format"/><xsl:text>",</xsl:text>
        <xsl:text>"filesize":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:size"/><xsl:text>",</xsl:text>
        <xsl:text>"checksum":"</xsl:text><xsl:value-of select="fits:fileinfo/fits:md5checksum"/><xsl:text>",</xsl:text>
        <xsl:text>"bitDepth":"</xsl:text><xsl:value-of select="fits:metadata/fits:video/fits:track[@type='video']/fits:bitDepth"/><xsl:text>",</xsl:text>
        <xsl:text>"colorSpace":"</xsl:text><xsl:value-of select="fits:metadata/fits:video/fits:track[@type='video']/fits:colorspace"/><xsl:text>",</xsl:text>
        <xsl:text>"duration-Ms":"</xsl:text><xsl:value-of select="fits:metadata/fits:audio/fits:duration"/><xsl:text>",</xsl:text>
        <xsl:text>"bitRate":"</xsl:text><xsl:value-of select="fits:metadata/fits:video/fits:bitrate"/><xsl:text>",</xsl:text>
        <xsl:text>"frameRate":"</xsl:text><xsl:value-of select="fits:metadata/fits:video/fits:track[@type='video']/fits:frameRate"/><xsl:text>",</xsl:text>
        <xsl:text>"chromaSubsampling":"</xsl:text><xsl:value-of select="fits:metadata/fits:video/fits:track[@type='video']/fits:chromaSubsampling"/><xsl:text>"}]</xsl:text>
    </xsl:template>
    
    
</xsl:stylesheet>